#!/usr/bin/env bash
# Resume configuration of the already installed Acer-specific Arch root.
set -euo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
rig_sources=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
rig_bootstrap=/mnt/rig-arch-bootstrap
rig_target=/mnt/rig-arch-target
rig_data=/var/lib/rig-arch
rig_debian_uuid=19fb6bca-4430-4e9f-be15-5a509c25c3ff
[[ $EUID -eq 0 ]]
[[ $(findmnt -nro UUID /) == "$rig_debian_uuid" ]]
rig_arch_uuid=$(cat "$rig_data/evidence/arch-root.uuid")
rig_backup=$(cat "$rig_data/evidence/debian-backup-path")
[[ $(findmnt -nro UUID "$rig_target") == "$rig_arch_uuid" ]]
[[ $(blkid -s LABEL -o value /dev/sda5) == RIG_ARCH ]]
[[ -x "$rig_target/usr/bin/pacman" ]]
cp /etc/resolv.conf "$rig_target/etc/resolv.conf"
cp "$rig_bootstrap/etc/pacman.d/mirrorlist" "$rig_target/etc/pacman.d/mirrorlist"
cat > "$rig_target/etc/fstab" <<EOF
UUID=$rig_arch_uuid / ext4 defaults 0 1
UUID=$rig_debian_uuid /srv/rig-data ext4 defaults 0 2
/srv/rig-data/var/lib/rig-arch/home /home none bind,x-systemd.requires-mounts-for=/srv/rig-data 0 0
/srv/rig-data/var/lib/rig-arch/pkg /var/cache/pacman/pkg none bind,x-systemd.requires-mounts-for=/srv/rig-data 0 0
/srv/rig-data/var/lib/rig-arch/swapfile none swap defaults 0 0
EOF
install -Dm700 "$rig_sources/configure-target.sh" "$rig_target/root/configure-target.sh"
install -Dm700 "$rig_sources/first-boot.sh" "$rig_target/usr/local/sbin/rig-arch-first-boot"
# Reuse password hashes locally; never print or log them.
awk -F: '$1 == "root" || $1 == "red-team-lab" { print $1 ":" $2 }' /etc/shadow > "$rig_target/root/rig-password-hashes"
if [[ -d /etc/NetworkManager/system-connections ]]; then
    mkdir -p "$rig_target/etc/NetworkManager/system-connections"
    cp -a /etc/NetworkManager/system-connections/. "$rig_target/etc/NetworkManager/system-connections/"
fi
chmod 755 "$rig_target" "$rig_target/etc"
if [[ ${1:-} != --configured ]]; then
    chroot "$rig_bootstrap" arch-chroot /mnt/target bash /root/configure-target.sh
else
    # Resume after completed account/system setup and separate user setup.
    chroot "$rig_bootstrap" arch-chroot /mnt/target id red-team-lab
    chmod 600 "$rig_target/root/rig-password-hashes"
    chroot "$rig_bootstrap" arch-chroot /mnt/target bash -c 'chpasswd -e < /root/rig-password-hashes; rm /root/rig-password-hashes'
fi
install -o1000 -g1000 -m600 "$rig_sources/minimal-config.py" "$rig_target/home/red-team-lab/.config/qtile/config.py"
install -o1000 -g1000 -m700 "$rig_sources/minimal-autostart.sh" "$rig_target/home/red-team-lab/.config/qtile/autostart.sh"
chmod 755 "$rig_target/etc/lightdm/lightdm.conf.d" "$rig_target/etc/X11/xorg.conf.d"
chmod 644 "$rig_target/etc/hosts" "$rig_target/etc/hostname" "$rig_target/etc/locale.conf" "$rig_target/etc/vconsole.conf" "$rig_target/etc/fstab" "$rig_target/etc/lightdm/lightdm.conf.d/50-rig-qtile.conf" "$rig_target/etc/X11/xorg.conf.d/10-rig-intel.conf" "$rig_target/etc/systemd/system/rig-arch-first-boot.service"
chroot "$rig_bootstrap" arch-chroot /mnt/target runuser -u red-team-lab -- env HOME=/home/red-team-lab python3 -c 'import runpy; runpy.run_path("/home/red-team-lab/.config/qtile/config.py")'
chroot "$rig_bootstrap" arch-chroot /mnt/target systemd-analyze verify /etc/systemd/system/rig-arch-first-boot.service
[[ $(df -B1 --output=avail "$rig_target" | tail -n1) -gt 2500000000 ]]
chroot "$rig_bootstrap" arch-chroot /mnt/target pacman -Qk base linux-lts qtile kitty networkmanager
chroot "$rig_bootstrap" arch-chroot /mnt/target runuser -u red-team-lab -- env HOME=/home/red-team-lab /home/red-team-lab/.local/bin/codex --version
[[ -s "$rig_target/boot/vmlinuz-linux-lts" && -s "$rig_target/boot/initramfs-linux-lts.img" ]]
printf '%s\n' 'INSTALLED_AND_CHECKED; physical boot validation pending.' > "$rig_data/evidence/install.status"

# Keep Debian as the saved default until first-boot verification succeeds.
mkdir -p /etc/default/grub.d
cat > /etc/default/grub.d/rig-arch.cfg <<'EOF'
GRUB_DEFAULT=saved
GRUB_SAVEDEFAULT=false
GRUB_TIMEOUT_STYLE=menu
GRUB_TIMEOUT=5
EOF
cat > /etc/grub.d/43_rig_arch_installed <<EOF
#!/bin/sh
exec tail -n +3 "\$0"
menuentry 'RIG: Arch Linux + Qtile' --id rig-arch-installed {
    insmod part_msdos
    insmod ext2
    search --no-floppy --fs-uuid --set=root $rig_arch_uuid
    linux /boot/vmlinuz-linux-lts root=UUID=$rig_arch_uuid rw panic=15
    initrd /boot/initramfs-linux-lts.img
}
EOF
chmod 755 /etc/grub.d/43_rig_arch_installed
grub-mkconfig -o "$rig_backup/grub.cfg.arch"
grub-script-check "$rig_backup/grub.cfg.arch"
grep -q -- '--id rig-arch-installed' "$rig_backup/grub.cfg.arch"
install -m600 "$rig_backup/grub.cfg.arch" /boot/grub/grub.cfg
grub-editenv /boot/grub/grubenv unset saved_entry
grub-reboot rig-arch-installed
sync
echo 'READY: installed Arch + Qtile selected for one boot; Debian fallback retained.'
echo 'Reboot is a separate action after reviewing the installation evidence.'
chroot "$rig_bootstrap" arch-chroot /mnt/target gpgconf --homedir /etc/pacman.d/gnupg --kill gpg-agent || true
sync
