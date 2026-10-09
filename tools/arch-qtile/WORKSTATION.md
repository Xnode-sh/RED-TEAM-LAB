# Рабочий набор RIG — 2026-10-09

Фактическая система: Acer Aspire E1-570G, Arch Linux, Qtile X11.
Установлены все 59 позиций из `packages-workstation.txt` и их зависимости.

- Интернет и связь: Firefox, Telegram Desktop, Blueman / BlueZ.
- Файлы: Thunar, предпросмотр Tumbler, GVfs/MTP, File Roller, 7zip, ZIP.
- Медиа: mpv, FFmpeg, Ristretto; текст: Mousepad, Neovim, Nano.
- Разработка: base-devel, CMake, Ninja, pip/pipx, GitHub CLI, jq, ripgrep, fd, fzf, tmux.
- Диагностика: btop, fastfetch, ncdu, duf, SMART, USB/PCI и сетевые инструменты.
- Рабочий стол: лёгкий Picom (XRender, без теней и анимаций), Flameshot, i3lock, шрифты Noto/emoji, Papirus Dark.

Firefox назначен браузером, Thunar — файловым менеджером; GTK использует тёмную тему.
Bluetooth включён, Blueman и Picom добавлены в автозапуск. В выпадающие меню панели добавлены приложения, Bluetooth и блокировка.

## Клавиши

- Super+B — Firefox.
- Super+E — Thunar.
- Super+Shift+S — выделение области в Flameshot.
- Print — снимок экрана через действие панели.
- Super+Escape — блокировка экрана.

## Проверка и восстановление

Firefox проверен запуском headless с отдельным временным профилем и сохранением PNG.
GCC собрал и запустил простую программу; FFmpeg создал H.264-видео, ffprobe подтвердил параметры.
Все четыре Polybar, Picom и Blueman работают; systemctl --failed не показывает ошибок.
После установки на корневом разделе свободно 6,1 GiB.

Пользовательская резервная копия: `~/.config/rig-backups/workstation-20261009-034559`.
Системная: `/var/backups/rig-workstation-20261009-034126`.
Pacman использует `/var/cache/pacman-rig`; исправлены права чтения ALPM_DB_VERSION после миграции.
Повторное применение пользовательских настроек: `python tools/arch-qtile/setup-workstation-user.py` от обычного пользователя в сеансе Qtile.

## Завершение миграции

2026-10-09 по команде оператора удалены системные файлы Debian; освобождено
7 137 800 192 байта. /dev/sda1 сохранён как RIG_DATA: домашние файлы, проект,
Codex и swap Arch продолжают использовать его. Закрытый архив старых настроек
и данных служб находится в /srv/rig-data/.migration-archive/, вне Git.
GRUB BIOS установлен из Arch в /dev/sda; hidden menu, timeout=1, default=0.
Проверены grub-script-check, успешный grub-install и Codex после очистки.
Перезагрузка и новый замер скорости ещё не выполнены.

## Автовызов RIG при старте

После входа в Qtile autostart.sh запускает codex-startup.sh в Kitty вместо
обычного пустого терминала. Защита от повторов допускает одно окно на загрузку.
В терминале выполняется ограниченный по времени git fetch origin и диагностика
загрузки; отчёт сохраняется в ~/.local/state/rig-codex/startup.txt.
Затем codex resume --last получает запрос прочитать протокол старта RIG,
сверить GitHub/PR и проверить загрузку Arch. Настройки sandbox/approvals наследуются.
Недоступность сети отмечается FETCH_FAILED; синхронизация не объявляется успешной.
Автовызов не выполняет merge, очистку, системные изменения или публикации.
Проверены синтаксис, однократный запуск и передача запроса через mock-команды;
фактический запуск на следующей загрузке ещё не проверен.
Отключение: заменить вызов codex-startup.sh в ~/.config/qtile/autostart.sh
на kitty --config "$HOME/.config/kitty/rig.conf" &.
