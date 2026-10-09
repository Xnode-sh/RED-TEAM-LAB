#!/usr/bin/env python3
"""Anchored GTK3 control cards opened by Polybar, with real system controls."""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, GLibUnix
from pathlib import Path
import math
import os
import signal
import subprocess
import sys
import threading
from datetime import datetime
from panel import ipc, read, run, GROUPS

HERE = Path(__file__).resolve().parent
RUNTIME = Path(os.environ.get('XDG_RUNTIME_DIR', f'/tmp/rig-panel-{os.getuid()}'))/'rig-polybar'

CSS = b'''
window { background: transparent; }
.card { background: #171923; border: 1px solid #363a4d; border-radius: 12px; padding: 14px; color: #eef3ff; }
label { color: #eef3ff; font-family: "DejaVu Sans"; font-size: 11px; }
.heading { font-size: 17px; font-weight: 700; }
.eyebrow { color: #b4a4ed; font-family: "JetBrains Mono"; font-size: 10px; letter-spacing: 1px; }
.muted { color: #8e9bb3; font-size: 11px; }
.number { font-size: 19px; font-weight: bold; color: #b4a4ed; }
.tile { background: #222532; border-radius: 8px; padding: 10px; }
button { background: #222532; border: 1px solid transparent; border-radius: 8px; padding: 8px; color: #eff4ff; box-shadow: none; }
button:hover { background: #253c50; border-color: #b4a4ed; }
button:active { background: #305b63; }
button label { font-size: 11px; }
.danger { background: #452035; }
.danger:hover { border-color: #ff375f; background: #60263f; }
.close { padding: 5px 9px; background: #222e43; }
image { color: #b4a4ed; }
scale { padding: 6px 0; }
scale trough { background: #293850; border-radius: 4px; min-height: 5px; }
scale highlight { background: #b4a4ed; border-radius: 5px; }
scale slider { background: #eef3ff; border: 1px solid #b4a4ed; min-height: 11px; min-width: 11px; border-radius: 50%; }
progressbar trough { background: #293850; border: none; min-height: 6px; border-radius: 4px; }
progressbar progress { background: #b4a4ed; border: none; min-height: 6px; border-radius: 4px; }
calendar { background: #222532; color: #eaf3ff; border-radius: 8px; padding: 8px; }
calendar:selected { background: #b4a4ed; color: #101722; }
calendar.header { color: #b4a4ed; }
'''

def label(text, style=None):
    obj = Gtk.Label(label=text, xalign=0)
    if style:
        obj.get_style_context().add_class(style)
    return obj

ICON_NAMES = {
    'view-app-grid-symbolic':'layout-grid','utilities-terminal-symbolic':'terminal',
    'system-run-symbolic':'bot','folder-symbolic':'folder','camera-photo-symbolic':'camera',
    'input-keyboard-symbolic':'keyboard','audio-volume-muted-symbolic':'volume-x',
    'audio-volume-high-symbolic':'volume-2','audio-input-microphone-symbolic':'mic',
    'audio-card-symbolic':'audio-lines','network-wireless-symbolic':'wifi',
    'network-wired-symbolic':'ethernet-port','utilities-system-monitor-symbolic':'cpu',
    'view-grid-symbolic':'layout-grid','view-restore-symbolic':'app-window',
    'view-fullscreen-symbolic':'maximize','view-dual-symbolic':'columns-2',
    'go-next-symbolic':'arrow-right','view-list-symbolic':'list',
    'system-log-out-symbolic':'log-out','system-reboot-symbolic':'rotate-cw',
    'system-shutdown-symbolic':'power','go-previous-symbolic':'rotate-cw',
}

def icon_pixbuf(name):
    path = HERE/'icons'/(ICON_NAMES[name]+'.svg')
    return GdkPixbuf.Pixbuf.new_from_file_at_scale(str(path),18,18,True)

class Card(Gtk.Window):
    def __init__(self, mode, anchor=None):
        super().__init__(type=Gtk.WindowType.POPUP)
        self.set_title('RIG / DROPDOWN')
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_accept_focus(True)
        self.set_can_focus(True)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.seat = Gdk.Display.get_default().get_default_seat()
        pointer = self.seat.get_pointer()
        _, px, py = pointer.get_position()
        monitor = Gdk.Display.get_default().get_monitor_at_point(px, py)
        self.geometry = monitor.get_geometry()
        self.anchor = px if anchor is None else anchor
        self.set_default_size(300, -1)
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.box.get_style_context().add_class('card')
        self.add(self.box)
        header = Gtk.Box(spacing=8)
        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        titles.pack_start(label('RED / LAB   •   RIG', 'eyebrow'),False,False,0)
        heading = {'workspaces':'Рабочие столы','apps':'Лаборатория','audio':'Звук','network':'Подключения',
                   'system':'Центр управления','calendar':'Календарь',
                   'power':'Завершение сеанса','windows':'Окна и раскладка'}[mode]
        titles.pack_start(label(heading,'heading'),False,False,0)
        header.pack_start(titles,True,True,0)
        close = Gtk.Button(label='×')
        close.get_style_context().add_class('close')
        close.set_valign(Gtk.Align.START)
        close.connect('clicked',lambda _:self.close_card())
        header.pack_end(close,False,False,0)
        self.box.pack_start(header,False,False,0)
        self.message = label('','muted')
        self.message.set_line_wrap(True)
        self.connect('destroy',lambda _:Gtk.main_quit())
        self.connect('key-press-event',self.key)
        self.connect('button-press-event',self.click)
        self.connect('size-allocate',self.position)
        self.connect('map-event',self.mapped)
        self.timers = {}
        getattr(self, mode)()
        self.box.pack_end(self.message,False,False,0)

    def close_card(self):
        self.seat.ungrab()
        self.destroy()

    def key(self, _, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close_card()
            return True
        return False

    def click(self, _, event):
        x,y = self.get_position()
        w,h = self.get_size()
        if not (x <= event.x_root < x+w and y <= event.y_root < y+h):
            self.close_card()
            return True
        return False

    def mapped(self, *_):
        self.seat.grab(self.get_window(),Gdk.SeatCapabilities.ALL,True,None,None,None,None)
        self.grab_focus()

    def position(self, _, allocation):
        g = self.geometry
        x = max(g.x+12,min(self.anchor-allocation.width//2,g.x+g.width-allocation.width-12))
        y = g.y+48
        self.move(x,min(y,g.y+g.height-allocation.height-12))
        # Rounded native X11 shape also works when no compositor is running.
        if not self.get_screen().is_composited() and self.get_window():
            try:
                import cairo
                region = cairo.Region()
                radius = 12
                for row in range(allocation.height):
                    edge = min(row,allocation.height-1-row)
                    inset = math.ceil(radius-math.sqrt(max(0,radius**2-(radius-edge-.5)**2))) if edge < radius else 0
                    region.union(cairo.RectangleInt(inset,row,allocation.width-2*inset,1))
                self.get_window().shape_combine_region(region,0,0)
            except ImportError:
                pass

    def button(self, title, icon, callback, subtitle=None, danger=False):
        button = Gtk.Button()
        row = Gtk.Box(spacing=9)
        row.pack_start(Gtk.Image.new_from_pixbuf(icon_pixbuf(icon)),False,False,0)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=3)
        text.pack_start(label(title),False,False,0)
        if subtitle:
            text.pack_start(label(subtitle,'muted'),False,False,0)
        row.pack_start(text,True,True,0)
        row.pack_end(label('›','muted'),False,False,0)
        button.add(row)
        if danger:
            button.get_style_context().add_class('danger')
        button.connect('clicked',lambda _:callback())
        self.box.pack_start(button,False,False,0)
        return button

    def execute(self, *args, after=None):
        def worker():
            try:
                subprocess.run(args,check=True,capture_output=True,text=True,timeout=8)
                if after:
                    GLib.idle_add(after)
            except (OSError,subprocess.SubprocessError):
                GLib.idle_add(self.message.set_text,'Не удалось применить настройку')
        threading.Thread(target=worker,daemon=True).start()

    def action(self, name):
        subprocess.Popen(['python',str(HERE/'actions.py'),name],start_new_session=True)
        self.close_card()

    def workspaces(self):
        grid=Gtk.Grid(column_spacing=6,row_spacing=6)
        current=ipc('get_screens')[0]['group']
        for n,name in enumerate(GROUPS):
            button=Gtk.Button(label=str(n+1))
            button.set_hexpand(True)
            if name==current:
                button.get_style_context().add_class('danger')
            def select(_,group=name):
                ipc('toscreen',selectors=[('group',group)])
                self.close_card()
            button.connect('clicked',select)
            grid.attach(button,n%5,n//5,1,1)
        self.box.pack_start(grid,False,False,0)

    def apps(self):
        self.box.pack_start(label('Инструменты и быстрый доступ','muted'),False,False,0)
        for title,icon,action,sub in [
            ('Приложения','view-app-grid-symbolic','apps','Поиск установленных программ'),
            ('Браузер','view-restore-symbolic','browser','Firefox'),
            ('Файлы','folder-symbolic','files','Thunar'),
            ('Telegram','view-list-symbolic','telegram','Telegram Desktop'),
            ('Терминал','utilities-terminal-symbolic','terminal','Kitty'),
            ('Codex','system-run-symbolic','codex','Продолжить работу над проектом'),
            ('Проект','folder-symbolic','project','RED-TEAM-LAB'),
            ('Снимок экрана','camera-photo-symbolic','screenshot','Сохранить PNG локально'),
            ('Горячие клавиши','input-keyboard-symbolic','help','Управление окнами и панелью')]:
            self.button(title,icon,lambda a=action:self.action(a),sub)

    def slider(self, title, value, callback):
        row = Gtk.Box(spacing=12)
        row.pack_start(label(title),True,True,0)
        amount = label(f'{value:.0f}%','eyebrow')
        row.pack_end(amount,False,False,0)
        self.box.pack_start(row,False,False,0)
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL,0,100,1)
        scale.set_draw_value(False)
        scale.set_value(value)
        def changed(obj):
            number = round(obj.get_value())
            amount.set_text(f'{number}%')
            if title in self.timers:
                GLib.source_remove(self.timers[title])
            def apply():
                self.timers.pop(title,None)
                callback(number)
                return False
            self.timers[title] = GLib.timeout_add(100,apply)
        scale.connect('value-changed',changed)
        self.box.pack_start(scale,False,False,0)

    def audio(self):
        result = run('wpctl','get-volume','@DEFAULT_AUDIO_SINK@')
        volume = min(100,float(result.split()[1])*100)
        self.box.pack_start(label('Встроенное аудио • PipeWire','muted'),False,False,0)
        self.slider('Громкость',volume,lambda n:self.execute('wpctl','set-volume','@DEFAULT_AUDIO_SINK@',f'{n}%'))
        self.sound_button = self.button('', 'audio-volume-muted-symbolic',
            lambda:self.execute('wpctl','set-mute','@DEFAULT_AUDIO_SINK@','toggle',after=self.sound_status))
        self.mic_button = self.button('', 'audio-input-microphone-symbolic',
            lambda:self.execute('wpctl','set-mute','@DEFAULT_AUDIO_SOURCE@','toggle',after=self.sound_status))
        self.sound_status()
        self.button('Аудиоустройства','audio-card-symbolic',lambda:self.action('audio-menu'),'Выходы, входы и состояние')

    def sound_status(self):
        for button,target,title in [(self.sound_button,'@DEFAULT_AUDIO_SINK@','Звук'),
                                     (self.mic_button,'@DEFAULT_AUDIO_SOURCE@','Микрофон')]:
            muted = 'MUTED' in run('wpctl','get-volume',target)
            # First label in the button's text column.
            button.get_child().get_children()[1].get_children()[0].set_text(title+(' выключен' if muted else ' включён'))
            if target=='@DEFAULT_AUDIO_SINK@':
                button.get_child().get_children()[0].set_from_pixbuf(icon_pixbuf('audio-volume-muted-symbolic' if muted else 'audio-volume-high-symbolic'))
        return False

    def network(self):
        status = run('nmcli','-t','-f','STATE,CONNECTIVITY','general')
        enabled = run('nmcli','radio','wifi') == 'enabled'
        self.box.pack_start(label('Подключено к сети' if status.startswith('connected') else 'Нет подключения','eyebrow'),False,False,0)
        self.button('Wi-Fi включён' if enabled else 'Wi-Fi выключен','network-wireless-symbolic',
                    lambda:self.execute('nmcli','radio','wifi','off' if enabled else 'on',after=self.close_card))
        self.box.pack_start(label('ДОСТУПНЫЕ СЕТИ','muted'),False,False,0)
        networks = run('nmcli','-t','-f','IN-USE,SIGNAL,SSID','device','wifi','list','--rescan','no')
        seen = set()
        for line in networks.splitlines():
            parts = line.split(':',2)
            if len(parts)!=3:
                continue
            active,strength,ssid = parts
            ssid = ssid.replace('\\:',':').replace('\\\\','\\')
            if not ssid or ssid in seen:
                continue
            seen.add(ssid)
            if len(seen)>4:
                break
            self.button(ssid,'network-wireless-symbolic',lambda s=ssid:self.connect_network(s),
                        f'{strength}% сигнала'+(' • подключена' if active=='*' else ''))
        if not seen:
            self.box.pack_start(label('Сети пока не обнаружены','muted'),False,False,0)
        self.button('Диагностика подключения','network-wired-symbolic',lambda:self.action('network'))
        self.button('Bluetooth','view-restore-symbolic',lambda:self.action('bluetooth'),'Устройства и подключения')

    def connect_network(self, ssid):
        # nmcli asks privately in a terminal; passwords never enter our files or logs.
        subprocess.Popen(['kitty','--title','RIG / Wi-Fi','nmcli','--ask','device','wifi','connect',ssid],start_new_session=True)
        self.close_card()

    def system(self):
        self.box.pack_start(label('Acer E1-570G • Arch Linux • ядро LTS','muted'),False,False,0)
        grid = Gtk.Grid(column_spacing=8,row_spacing=8)
        self.stats = {}
        for index,name in enumerate(('CPU','RAM','TEMP','ROOT')):
            tile = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8)
            tile.get_style_context().add_class('tile')
            tile.set_hexpand(True)
            tile.pack_start(label(name,'muted'),False,False,0)
            number = label('—','number')
            tile.pack_start(number,False,False,0)
            self.stats[name] = number
            grid.attach(tile,index%2,index//2,1,1)
        self.box.pack_start(grid,False,False,0)
        self.cpu_previous = None
        self.update_stats()
        GLib.timeout_add_seconds(2,self.update_stats)
        for path in Path('/sys/class/backlight').glob('*'):
            self.slider('Яркость',int(read(path/'brightness'))*100/int(read(path/'max_brightness')),
                        lambda n:self.execute('brightnessctl','set',f'{max(1,n)}%'))
            break
        self.button('Процессы и нагрузка','utilities-system-monitor-symbolic',lambda:self.action('monitor'),'Открыть htop')
        self.button('Окна и раскладка','view-grid-symbolic',lambda:self.replace('windows'))

    def update_stats(self):
        values=list(map(int,read('/proc/stat').splitlines()[0].split()[1:9]))
        now=(sum(values),values[3]+values[4])
        if self.cpu_previous:
            total,idle=now[0]-self.cpu_previous[0],now[1]-self.cpu_previous[1]
            self.stats['CPU'].set_text(f'{100*(1-idle/max(1,total)):.0f}%')
        self.cpu_previous=now
        mem={k:int(v.split()[0]) for k,v in (line.split(':',1) for line in read('/proc/meminfo').splitlines())}
        self.stats['RAM'].set_text(f'{(mem["MemTotal"]-mem["MemAvailable"])/1024**2:.1f} ГБ')
        temps=[]
        for hw in Path('/sys/class/hwmon').glob('*'):
            if read(hw/'name')=='coretemp':
                temps.extend(int(read(p))/1000 for p in hw.glob('temp*_input') if read(p).isdigit())
        self.stats['TEMP'].set_text(f'{max(temps):.0f}°C' if temps else '—')
        st=os.statvfs('/')
        self.stats['ROOT'].set_text(f'{st.f_bavail*st.f_frsize/1024**3:.1f} ГБ')
        return True

    def replace(self, mode):
        anchor = self.anchor
        self.close_card()
        subprocess.Popen(['python',str(HERE/'dropdown.py'),mode,'--anchor',str(anchor)],start_new_session=True)

    def windows(self):
        for title,icon,obj,cmd in [
            ('Повернуть разделение','view-grid-symbolic','layout','toggle_split'),
            ('Плавающий / плиточный режим','view-restore-symbolic','window','toggle_floating'),
            ('Полный экран','view-fullscreen-symbolic','window','toggle_fullscreen'),
            ('Выровнять размеры','view-dual-symbolic','layout','normalize'),
            ('Следующее окно','go-next-symbolic','group','next_window'),
            ('Список окон','view-list-symbolic',None,None)]:
            def apply(o=obj,c=cmd):
                if o:
                    ipc(c,selectors=[(o,None)])
                    self.close_card()
                else:
                    self.action('windows')
            self.button(title,icon,apply)

    def calendar(self):
        self.box.pack_start(label(datetime.now().strftime('%d.%m.%Y  •  %H:%M'),'eyebrow'),False,False,0)
        widget=Gtk.Calendar()
        now=datetime.now()
        widget.mark_day(now.day)
        self.box.pack_start(widget,False,False,0)

    def power(self):
        self.button('Заблокировать экран','view-restore-symbolic',lambda:self.action('lock'))
        self.box.pack_start(label('Сохрани работу перед завершением сеанса','muted'),False,False,0)
        for title,icon,command in [('Выйти из Qtile','system-log-out-symbolic','logout'),
                                 ('Перезагрузить','system-reboot-symbolic','reboot'),
                                 ('Выключить','system-shutdown-symbolic','poweroff')]:
            self.button(title,icon,lambda c=command,t=title:self.confirm_power(c,t),danger=True)

    def confirm_power(self, command, title):
        for child in self.box.get_children()[1:]:
            self.box.remove(child)
        self.box.pack_start(label(title+'?','heading'),False,False,0)
        self.box.pack_start(label('Несохранённая работа будет потеряна.','muted'),False,False,0)
        def apply():
            if command=='logout':
                ipc('shutdown')
            else:
                subprocess.Popen(['systemctl',command])
            self.close_card()
        self.button('Подтвердить','system-shutdown-symbolic',apply,danger=True)
        self.button('Отмена','go-previous-symbolic',lambda:self.replace('power'))
        self.show_all()

def main():
    mode=sys.argv[1]
    RUNTIME.mkdir(parents=True,exist_ok=True)
    pidfile=RUNTIME/'dropdown.pid'
    try:
        old=int(pidfile.read_text())
        cmd=Path(f'/proc/{old}/cmdline').read_bytes()
        if str(HERE/'dropdown.py').encode() in cmd:
            os.kill(old,signal.SIGTERM)
    except (OSError,ValueError):
        pass
    pidfile.write_text(str(os.getpid()))
    anchor=int(sys.argv[sys.argv.index('--anchor')+1]) if '--anchor' in sys.argv else None
    card=Card(mode,anchor)
    card.show_all()
    GLibUnix.signal_add(GLib.PRIORITY_DEFAULT,signal.SIGTERM,lambda:card.close_card())
    Gtk.main()
    if pidfile.exists() and pidfile.read_text()==str(os.getpid()):
        pidfile.unlink()

if __name__=='__main__':
    main()
