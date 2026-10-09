"""RIG Qtile X11: prepared configuration; live hardware validation is pending."""
from pathlib import Path
import os
import subprocess
import xcffib
import xcffib.xkb

from libqtile import bar, hook, layout, widget
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.lazy import lazy

mod = "mod4"
terminal = f"kitty --config {Path.home()}/.config/kitty/rig.conf"
project = Path.home() / "RED-TEAM-LAB"
os.environ["RIG_CAPTURE_SYSTEM_FFMPEG"] = "1"
keys = [
    Key([mod], "Return", lazy.spawn(terminal)),
    Key([mod], "space", lazy.spawn("rofi -show drun")),
    Key([mod], "Tab", lazy.spawn("rofi -show window")),
    Key([mod], "q", lazy.window.kill()),
    Key([mod], "f", lazy.window.toggle_fullscreen()),
    Key([mod, "shift"], "space", lazy.window.toggle_floating()),
    Key([mod], "j", lazy.layout.down()),
    Key([mod], "k", lazy.layout.up()),
    Key([mod], "h", lazy.layout.left()),
    Key([mod], "l", lazy.layout.right()),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down()),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up()),
    Key([mod, "control"], "r", lazy.reload_config()),
    Key([mod], "t", lazy.next_layout()),
    Key([mod, "shift"], "a", lazy.spawn(f"python3 {project}/tools/local-ai/launch.py")),
    Key([mod, "shift"], "s", lazy.spawn(f"python3 {project}/tools/i3/scripts/capture.py area")),
    Key([mod, "shift"], "r", lazy.spawn(f"python3 {project}/tools/i3/scripts/capture.py toggle")),
    Key([mod, "shift"], "v", lazy.spawn("kitty --class rig-cava cava")),
    Key([mod, "shift"], "c", lazy.spawn(f"{terminal} {Path.home()}/.local/bin/rig-codex")),
    Key([], "XF86AudioRaiseVolume", lazy.spawn("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+")),
    Key([], "XF86AudioLowerVolume", lazy.spawn("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-")),
    Key([], "XF86AudioMute", lazy.spawn("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle")),
    Key([], "XF86MonBrightnessUp", lazy.spawn("brightnessctl set +5%")),
    Key([], "XF86MonBrightnessDown", lazy.spawn("brightnessctl set 5%-")),
]
groups = [
    Group("CODE"), Group("LAB"),
    Group("AI", matches=[Match(wm_class="rig-local-ai")]),
    Group("COMMS", matches=[Match(wm_class="TelegramDesktop")]),
    Group("SYS"),
]
for index, group in enumerate(groups, 1):
    keys.extend([
        Key([mod], str(index), lazy.group[group.name].toscreen()),
        Key([mod, "shift"], str(index), lazy.window.togroup(group.name)),
    ])
theme = dict(border_focus="#23dcc8", border_normal="#252c40", border_width=2, margin=6)
layouts = [layout.MonadTall(**theme), layout.Columns(**theme), layout.Max()]
widget_defaults = dict(font="DejaVu Sans Mono", fontsize=12, padding=6)
extension_defaults = widget_defaults.copy()


def recording_status():
    try:
        result = subprocess.run(
            ["python3", str(project / "tools/i3/scripts/capture.py"), "status-plain"],
            capture_output=True, text=True, timeout=2, check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "REC ?"


def keyboard_state():
    connection = None
    try:
        connection = xcffib.connect()
        keyboard = connection(xcffib.xkb.key)
        keyboard.UseExtension(1, 0).reply()
        group = keyboard.GetState(0x100).reply().group
        return ("EN", "RU")[group] if group in (0, 1) else "KB ?"
    except (xcffib.Error, xcffib.ConnectionException, OSError):
        return "KB ?"
    finally:
        if connection is not None:
            connection.disconnect()


screens = [Screen(top=bar.Bar([
    widget.TextBox("RIG / LAB", foreground="#23dcc8"),
    widget.GroupBox(highlight_method="line", active="#e4e8f1"),
    widget.CurrentLayout(),
    widget.WindowName(),
    widget.CPU(format="CPU {load_percent}%", update_interval=5),
    widget.Memory(format="RAM {MemUsed:.0f}{mm}", update_interval=5),
    widget.GenPollText(func=recording_status, update_interval=2, foreground="#ff6582"),
    widget.GenPollText(func=keyboard_state, update_interval=1),
    widget.Clock(format="%d.%m %H:%M"),
    widget.Systray(),
], 28, background="#10131d"))]
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]
floating_layout = layout.Floating(float_rules=[
    *layout.Floating.default_float_rules,
    Match(wm_class="rig-cava"),
])
follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True
wmname = "LG3D"


@hook.subscribe.startup_once
def autostart():
    script = Path(__file__).with_name("autostart.sh")
    if script.is_file():
        subprocess.Popen(["bash", str(script)])
