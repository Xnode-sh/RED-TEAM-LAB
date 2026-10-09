"""RIG desktop with active-window binary tiling and directional controls."""
from pathlib import Path
import subprocess
import shutil
from libqtile import bar, hook, layout, widget
from libqtile.config import Click, Drag, Group, Key, Screen
from libqtile.lazy import lazy

mod = "mod4"
terminal = f"kitty --config {Path.home()}/.config/kitty/rig.conf"
keys = [
    Key([mod], "Return", lazy.spawn(terminal)),
    Key([mod], "b", lazy.spawn("firefox")),
    Key([mod], "e", lazy.spawn("thunar")),
    Key([mod, "shift"], "s", lazy.spawn("flameshot gui")),
    Key([mod], "Escape", lazy.spawn("i3lock --color 171923")),
    Key([], "Print", lazy.spawn(f"python {Path.home()}/.config/polybar/rig/actions.py screenshot")),
    Key([mod], "space", lazy.spawn("rofi -show drun")),
    Key([mod], "q", lazy.window.kill()),
    Key([mod], "f", lazy.window.toggle_fullscreen()),
    Key([mod], "j", lazy.layout.down()),
    Key([mod], "k", lazy.layout.up()),
    Key([mod], "h", lazy.layout.left()),
    Key([mod], "l", lazy.layout.right()),
    Key([mod, "shift"], "space", lazy.window.toggle_floating()),
    Key([mod], "v", lazy.window.toggle_floating()),
    Key([mod], "o", lazy.layout.toggle_split()),
    Key([mod], "s", lazy.layout.toggle_split()),
    Key([mod, "shift"], "n", lazy.layout.normalize()),
    Key([mod, "control"], "r", lazy.reload_config()),
    Key([mod, "shift"], "c", lazy.spawn(f"{terminal} {Path.home()}/.local/bin/rig-codex --last")),
    Key([], "XF86AudioRaiseVolume", lazy.spawn("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+")),
    Key([], "XF86AudioLowerVolume", lazy.spawn("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-")),
    Key([], "XF86AudioMute", lazy.spawn("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle")),
    Key([], "XF86MonBrightnessUp", lazy.spawn("brightnessctl set +5%")),
    Key([], "XF86MonBrightnessDown", lazy.spawn("brightnessctl set 5%-")),
]
for direction, letter, dx, dy in (
    ("left", "h", -30, 0), ("down", "j", 0, 30),
    ("up", "k", 0, -30), ("right", "l", 30, 0),
):
    arrow = direction.capitalize()
    keys.append(Key([mod], arrow, getattr(lazy.layout, direction)()))
    for key in (arrow, letter):
        keys.append(Key(
            [mod, "shift"], key,
            getattr(lazy.layout, f"shuffle_{direction}")().when(when_floating=False),
            lazy.window.move_floating(dx, dy).when(when_floating=True),
        ))
        keys.append(Key(
            [mod, "control"], key,
            getattr(lazy.layout, f"grow_{direction}")().when(when_floating=False),
            lazy.window.resize_floating(dx, dy).when(when_floating=True),
        ))
keys.extend([
    Key([mod], "Tab", lazy.group.next_window()),
    Key([mod, "shift"], "Tab", lazy.group.prev_window()),
    Key([mod, "mod1"], "Tab", lazy.spawn("rofi -show window")),
    Key([mod], "bracketright", lazy.screen.next_group()),
    Key([mod], "bracketleft", lazy.screen.prev_group()),
])
# Preserve existing group names so reloading keeps current windows in place.
groups = [Group(name) for name in ("CODE", "LAB", "COMMS", "SYS", "5", "6", "7", "8", "9", "10")]
for index, group in enumerate(groups, 1):
    keys.extend([
        Key([mod], str(index % 10), lazy.group[group.name].toscreen()),
        Key([mod, "shift"], str(index % 10), lazy.window.togroup(group.name, switch_group=True)),
        Key([mod, "shift", "control"], str(index % 10), lazy.window.togroup(group.name)),
    ])
theme = dict(border_focus="#23dcc8", border_normal="#252c40", border_width=2, margin=6)
layouts = [layout.Bsp(name="dwindle", fair=False, ratio=1.0,
                      lower_right=True, grow_amount=5, border_on_single=True, **theme)]
floating_layout = layout.Floating(**theme)
widget_defaults = dict(font="DejaVu Sans Mono", fontsize=12, padding=6)
screens = [Screen(top=bar.Bar([
    widget.TextBox("RIG / ARCH", foreground="#23dcc8"),
    widget.GroupBox(highlight_method="line", active="#e4e8f1"),
    widget.CurrentLayout(), widget.WindowName(),
    widget.CPU(format="CPU {load_percent}%", update_interval=5),
    widget.Memory(format="RAM {MemUsed:.0f}{mm}", update_interval=5),
    widget.Clock(format="%d.%m %H:%M"), widget.Systray(),
], 28, background="#10131d"))]
# External Polybar docks reserve their own space through EWMH struts.
# Keep the native bar available as a fallback when Polybar is not installed.
if shutil.which("polybar"):
    screens = [Screen(top=bar.Gap(40), bottom=bar.Gap(32))]
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]
follow_mouse_focus = True
auto_fullscreen = True
wmname = "LG3D"


@hook.subscribe.startup_once
def autostart():
    script = Path(__file__).with_name("autostart.sh")
    if script.is_file():
        subprocess.Popen(["bash", str(script)])
