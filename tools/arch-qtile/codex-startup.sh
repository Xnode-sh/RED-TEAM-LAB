#!/usr/bin/env bash
# One RIG terminal per boot; synchronization never blocks desktop startup.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
rig_project="$HOME/RED-TEAM-LAB"
rig_script="$rig_project/tools/arch-qtile/codex-startup.sh"
rig_runtime="${XDG_RUNTIME_DIR:-/tmp/rig-codex-$UID}/rig-codex"
umask 077
mkdir -p "$rig_runtime"
if [[ ${1:-} != --terminal ]]; then
    [[ -n ${DISPLAY:-} && -x "$HOME/.local/bin/codex" && -d "$rig_project/.git" ]] || exit 1
    rig_boot=$(cat /proc/sys/kernel/random/boot_id)
    rig_marker="$rig_runtime/started-$rig_boot"
    mkdir "$rig_marker" 2>/dev/null || exit 0
    if ! kitty --config "$HOME/.config/kitty/rig.conf" --title 'RIG / STARTUP SYNC' \
        --directory "$rig_project" bash "$rig_script" --terminal; then
        rmdir "$rig_marker"
        exit 1
    fi
    exit 0
fi
exec 9>"$rig_runtime/session.lock"
flock -n 9 || exit 0
cd "$rig_project"
rig_state="${XDG_STATE_HOME:-$HOME/.local/state}/rig-codex"
mkdir -p "$rig_state"
rig_report="$rig_state/startup.txt"
{
    date -u '+Startup: %Y-%m-%d %H:%M:%S UTC'
    printf '\nLOCAL\n'
    git status --short --branch
    git log -1 --oneline
    printf '\nBOOT\n'
    systemd-analyze || true
    systemctl --failed --no-pager || true
    printf '\nGITHUB FETCH\n'
    # Bound retries for Wi-Fi; do not delay the desktop or change working files.
    rig_fetched=false
    for rig_attempt in 1 2 3; do
        if GIT_TERMINAL_PROMPT=0 timeout 15 git fetch origin; then
            rig_fetched=true
            break
        fi
        [[ $rig_attempt == 3 ]] || sleep 3
    done
    if $rig_fetched; then
        echo 'FETCH_OK'
        git status --short --branch
        git log -1 --oneline origin/main
    else
        echo 'FETCH_FAILED: remote state is unverified; continue with local context.'
    fi
} > "$rig_report" 2>&1
cat "$rig_report"
rig_prompt="Автовызов после загрузки Acer. Ты RIG, локальный Systems & Linux Environment Engineer; установлен Arch + Qtile. Определи идентичность по фактической среде, не по названию Codex. Прочитай AGENTS.md → agents/RIG/ROLE.md → STATE.md → MEMORY.md → SYNC.md, затем TEAM.md, WORKFLOW.md, SECURITY.md и docs/HQ.md. Исторические упоминания Debian не доказывают текущую ОС. Прочитай локальный отчёт $rig_report: fetch выполнен до запуска, проверь FETCH_OK/FETCH_FAILED. Сверь локальную ветку, origin/main, открытые PR #16/#17 и актуальные задачи; сохрани незакоммиченные данные. Проверь загрузку Arch после переноса GRUB, systemd-analyze и failed units; Debian удалён, данные сохранены. При отсутствии сети явно отметь, что GitHub не синхронизирован. Обнови собственные STATE/MEMORY/SYNC проверенными фактами и выдай краткий отчёт на русском. Не выполняй merge, очистку, системные изменения или публикации автоматически. После проверки ожидай оператора."
"$HOME/.local/bin/codex" resume --last "$rig_prompt"
