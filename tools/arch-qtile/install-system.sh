#!/usr/bin/env bash
# Run only after Arch has been installed and booted. Does not partition disks.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Run with sudo on the installed Arch system.' >&2; exit 1; }
source /etc/os-release
[[ "$ID" == arch && ! -d /run/archiso ]] || { echo 'Requires installed Arch, not Debian or the Live installer.' >&2; exit 1; }
pacman -Syu --needed \
    linux-lts intel-ucode linux-firmware mesa libva-intel-driver mesa-utils \
    xorg-server xorg-xinit xorg-xrandr xorg-setxkbmap xf86-input-libinput \
    qtile python-psutil kitty rofi picom dunst feh cava \
    ttf-dejavu ttf-jetbrains-mono \
    lightdm lightdm-gtk-greeter \
    networkmanager network-manager-applet \
    pipewire pipewire-alsa pipewire-pulse wireplumber pavucontrol \
    xfce4-power-manager brightnessctl acpi \
    thunar gvfs xfce4-screenshooter ffmpeg xdg-utils xdg-user-dirs \
    git github-cli openssh rsync gnupg curl wget ripgrep \
    base-devel cmake ninja python python-pip nodejs npm firefox \
    gnome-keyring libsecret polkit-gnome
systemctl enable NetworkManager lightdm
echo 'Packages installed. Run install-user.sh as red-team-lab, then reboot to test Qtile X11.'
