#!/usr/bin/env bash
set -euo pipefail
umask 077
source /etc/os-release
[[ $ID == arch && $EUID -eq 0 && -f /root/rig-password-hashes ]]
ln -sf /usr/share/zoneinfo/Europe/Kyiv /etc/localtime
printf 'en_US.UTF-8 UTF-8\nru_RU.UTF-8 UTF-8\nuk_UA.UTF-8 UTF-8\n' > /etc/locale.gen
locale-gen
printf 'LANG=en_US.UTF-8\n' > /etc/locale.conf
printf 'KEYMAP=us\n' > /etc/vconsole.conf
printf 'rig-arch\n' > /etc/hostname
printf '127.0.0.1 localhost\n::1 localhost\n127.0.1.1 rig-arch\n' > /etc/hosts
getent group red-team-lab >/dev/null || groupadd -g 1000 red-team-lab
groupadd -f autologin
if ! id red-team-lab >/dev/null 2>&1; then
    useradd -u 1000 -g red-team-lab -G wheel,audio,video,autologin -d /home/red-team-lab -s /bin/bash red-team-lab
fi
[[ $(id -u red-team-lab) == 1000 ]]
usermod -aG wheel,audio,video,autologin red-team-lab
chpasswd -e < /root/rig-password-hashes
rm /root/rig-password-hashes
install -d -m750 /etc/sudoers.d
printf '%%wheel ALL=(ALL:ALL) ALL\n' > /etc/sudoers.d/10-rig-wheel
chmod 440 /etc/sudoers.d/10-rig-wheel
visudo -cf /etc/sudoers
mkdir -p /etc/lightdm/lightdm.conf.d
cat > /etc/lightdm/lightdm.conf.d/50-rig-qtile.conf <<'EOF'
[Seat:*]
user-session=qtile
autologin-user=red-team-lab
autologin-user-timeout=0
autologin-session=qtile
EOF
mkdir -p /etc/X11/xorg.conf.d
cat > /etc/X11/xorg.conf.d/10-rig-intel.conf <<'EOF'
Section "OutputClass"
    Identifier "RIG Intel display"
    MatchDriver "i915"
    Driver "modesetting"
    Option "PrimaryGPU" "yes"
EndSection
EOF
# Build a portable initramfs: autodetect in a Debian chroot is insufficient.
cat > /etc/mkinitcpio.conf <<'EOF'
MODULES=(ahci ext4 i915)
BINARIES=()
FILES=()
HOOKS=(base udev microcode modconf kms keyboard keymap consolefont block filesystems fsck)
EOF
mkinitcpio -P
systemctl enable NetworkManager lightdm
systemctl set-default graphical.target
cat > /etc/systemd/system/rig-arch-first-boot.service <<'EOF'
[Unit]
Description=Verify RIG Arch migration and select its permanent boot entry
After=NetworkManager.service lightdm.service
OnFailure=rig-arch-recover.service
RequiresMountsFor=/srv/rig-data /home
ConditionPathExists=!/srv/rig-data/var/lib/rig-arch/evidence/first-boot.ok

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/rig-arch-first-boot
TimeoutStartSec=240

[Install]
WantedBy=graphical.target
EOF
systemctl enable rig-arch-first-boot.service
install -m644 /home/red-team-lab/RED-TEAM-LAB/tools/arch-qtile/rig-arch-recover.service /etc/systemd/system/rig-arch-recover.service
runuser -u red-team-lab -- env HOME=/home/red-team-lab bash /home/red-team-lab/RED-TEAM-LAB/tools/arch-qtile/install-user.sh
install -o1000 -g1000 -m600 /home/red-team-lab/RED-TEAM-LAB/tools/arch-qtile/minimal-config.py /home/red-team-lab/.config/qtile/config.py
install -o1000 -g1000 -m700 /home/red-team-lab/RED-TEAM-LAB/tools/arch-qtile/minimal-autostart.sh /home/red-team-lab/.config/qtile/autostart.sh
runuser -u red-team-lab -- env HOME=/home/red-team-lab python3 -c 'import runpy; runpy.run_path("/home/red-team-lab/.config/qtile/config.py")'
systemd-analyze verify /etc/systemd/system/rig-arch-first-boot.service
echo 'TARGET CONFIGURED: minimal Qtile, native Codex, and first-boot verification.'
