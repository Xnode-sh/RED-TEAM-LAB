#!/usr/bin/env python3
"""Agent automation engine — RED └•TEAM•┐ lab™.

Автоматизирует протоколы системы совместной работы (docs/COLLABORATION.md):
boot + self-check + startup report, auto-save (checkpoint), handoff и file lock.

Не меняет роли и архитектуру — только читает и обновляет уже существующие файлы
по документированным протоколам. Отсутствующие файлы не приводят к падению.

Использование:
  python3 scripts/agent.py boot [--name NAME]
  python3 scripts/agent.py checkpoint --last "..." --next "..." [--name NAME]
                                      [--blockers "..."] [--memory "..."]
                                      [--commit SHA] [--branch B] [--pr PR]
  python3 scripts/agent.py handoff --to NAME --task T-xxx --next "..."
                                   [--from NAME] [--status S] [--blockers B]
                                   [--files "a,b"] [--append]
  python3 scripts/agent.py lock <path> [--name NAME] [--task T-xxx]
  python3 scripts/agent.py unlock <path> [--name NAME]
  python3 scripts/agent.py locks
"""
from __future__ import annotations
import argparse
import datetime
import os
import platform
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS = ["RIG", "KAI", "NOVA", "ORBIT"]
AGENT_FILES = ["ROLE.md", "STATE.md", "MEMORY.md", "SYNC.md"]
LOCKS_FILE = os.path.join(ROOT, "docs", "LOCKS.md")
LOCK_HEADER_KEY = "Файл / путь"


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def read_text(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return None


# ---------------------------------------------------------------- identity ---

def detect_identity() -> tuple[str | None, str]:
    """Определить личность по среде (AGENTS.md). Возвращает (NAME|None, причина)."""
    env = os.environ.get("LAB_AGENT")
    if env and env.upper() in AGENTS:
        return env.upper(), f"задано LAB_AGENT={env.upper()}"
    uname = " ".join(platform.uname()).lower()
    # Эвристики по таблице сред AGENTS.md (не присваивать чужую личность при неопределённости).
    if "proot-distro" in uname or "proot" in uname:
        return "KAI", "обнаружена среда Termux → Ubuntu/proot (PRoot-Distro)"
    if "debian" in uname:
        return "RIG", "обнаружена среда Debian"
    return None, "среда не распознана — личность не присвоена (уточнить у оператора)"


# ------------------------------------------------------------- parsing -------

def parse_sync_table(text: str) -> dict:
    """SYNC.md: таблица '| Поле | Значение |' -> dict."""
    data = {}
    if not text:
        return data
    for line in text.splitlines():
        m = re.match(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", line)
        if not m:
            continue
        key, val = m.group(1).strip(), m.group(2).strip()
        if key in ("Поле", "") or set(key) <= set("-: "):
            continue
        data[key] = val
    return data


def parse_state_bullets(text: str) -> dict:
    data = {}
    if not text:
        return data
    for line in text.splitlines():
        m = re.match(r"^[-*]\s*([^:]+):\s*(.+)$", line)
        if m:
            data[m.group(1).strip()] = m.group(2).strip()
    return data


def parse_role(text: str) -> tuple[str, str]:
    """Вернуть (role, mission)."""
    role, mission = "—", "—"
    if not text:
        return role, mission
    m = re.search(r"Роль:\s*\*\*(.+?)\*\*", text)
    if m:
        role = m.group(1).strip()
    else:
        h = re.search(r"^#\s*\w+\s*—\s*(.+)$", text, re.M)
        if h:
            role = h.group(1).strip()
    mm = re.search(r"^##\s*Mission\s*\n+(.+)", text, re.M)
    if mm:
        mission = mm.group(1).strip()
    else:
        mission = role
    return role, mission


# ------------------------------------------------------------- boot ----------

def cmd_boot(args) -> int:
    name = (args.name or "").upper() or None
    reason = "задано --name" if name else ""
    if not name:
        name, reason = detect_identity()

    print("=== AGENT BOOT ===")
    agents_md = read_text(os.path.join(ROOT, "AGENTS.md"))
    print(f"[1] AGENTS.md: {'прочитан' if agents_md else 'ОТСУТСТВУЕТ'}")
    print(f"[2] Личность: {name or 'НЕ ОПРЕДЕЛЕНА'} ({reason})")

    files_read, missing = [], []
    contents = {}
    if name:
        for i, f in enumerate(AGENT_FILES, start=3):
            p = os.path.join(ROOT, "agents", name, f)
            txt = read_text(p)
            rels = f"agents/{name}/{f}"
            if txt is None:
                missing.append(rels)
                print(f"[{i}] {rels}: ОТСУТСТВУЕТ (пропуск, не падаем)")
            else:
                files_read.append(rels)
                contents[f] = txt
                print(f"[{i}] {rels}: прочитан")
    else:
        print("    Файлы агента не читаются: личность не определена.")

    role, mission = parse_role(contents.get("ROLE.md", ""))
    sync = parse_sync_table(contents.get("SYNC.md", ""))
    state = parse_state_bullets(contents.get("STATE.md", ""))

    def pick(*vals, default="—"):
        for v in vals:
            if v:
                return v
        return default

    status = pick(state.get("Статус"), "booted" if name else "identity-unknown")
    current = pick(sync.get("Текущая миссия"), state.get("Активная задача"))
    last_action = pick(sync.get("Последняя завершённая задача"))
    last_update = pick(sync.get("Время последнего обновления"))
    blockers = pick(sync.get("Известные блокеры"), "нет")
    next_step = pick(sync.get("Следующий шаг"), state.get("Следующий шаг"))

    print("\n=== STARTUP REPORT ===")
    print(f"STATUS:       {status}")
    print(f"ROLE:         {role}")
    print(f"MISSION:      {mission}")
    print(f"CURRENT TASK: {current}")
    print(f"LAST ACTION:  {last_action}")
    print(f"LAST UPDATE:  {last_update}")
    print(f"BLOCKERS:     {blockers}")
    print(f"FILES READ:   {', '.join(['AGENTS.md'] + files_read) if agents_md else ', '.join(files_read)}")
    print(f"NEXT STEP:    {next_step}")
    if missing:
        print(f"\nПРЕДУПРЕЖДЕНИЕ: отсутствуют файлы: {', '.join(missing)}")
    return 0


# --------------------------------------------------------- checkpoint --------

def _update_sync(name: str, args) -> list[str]:
    path = os.path.join(ROOT, "agents", name, "SYNC.md")
    text = read_text(path)
    changed = []
    if text is None:
        return [f"SYNC.md отсутствует у {name} — пропуск"]
    repl = {
        "Последняя завершённая задача": args.last,
        "Следующий шаг": args.next,
        "Известные блокеры": args.blockers,
        "Время последнего обновления": now_utc(),
        "Commit SHA": args.commit,
        "Branch": args.branch,
        "PR": args.pr,
    }
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", line)
        if not m:
            continue
        key = m.group(1).strip()
        if key in repl and repl[key]:
            lines[i] = f"| {key} | {repl[key]} |"
            changed.append(key)
    if changed:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + ("\n" if text.endswith("\n") else ""))
    return changed


def _append_memory(name: str, note: str) -> bool:
    path = os.path.join(ROOT, "agents", name, "MEMORY.md")
    text = read_text(path)
    if text is None:
        return False
    stamp = datetime.date.today().isoformat()
    entry = f"- {stamp} — {note}\n"
    if "## История задач" in text:
        text = text.rstrip("\n") + "\n" + entry
    else:
        text = text.rstrip("\n") + "\n\n## История задач\n\n" + entry
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return True


def _update_state(name: str, args) -> list[str]:
    """Обновить машинный блок STATE:BEGIN..STATE:END, не трогая прозу."""
    path = os.path.join(ROOT, "agents", name, "STATE.md")
    text = read_text(path)
    if text is None:
        return ["STATE.md отсутствует"]
    lines = text.splitlines()
    try:
        b = next(i for i, l in enumerate(lines) if "STATE:BEGIN" in l)
        e = next(i for i, l in enumerate(lines) if "STATE:END" in l)
    except StopIteration:
        return ["нет машинного блока STATE:BEGIN/END"]
    repl = {
        "Статус (машинно):": args.status,
        "Активная задача (машинно):": args.active,
        "Следующий шаг (машинно):": args.next,
        "Обновлено (машинно):": now_utc(),
    }
    changed = []
    for i in range(b + 1, e):
        for key, val in repl.items():
            if val and lines[i].lstrip().startswith(f"- {key}"):
                lines[i] = f"- {key} {val}"
                changed.append(key.rstrip(" :"))
    if changed:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + ("\n" if text.endswith("\n") else ""))
    return changed


def cmd_checkpoint(args) -> int:
    name = (args.name or "").upper() or detect_identity()[0]
    if not name:
        print("checkpoint: личность не определена — укажите --name")
        return 1
    print(f"=== SESSION CHECKPOINT ({name}) ===")
    changed = _update_sync(name, args)
    print(f"SYNC.md обновлено: {', '.join(changed) if changed else 'без изменений'}")
    if args.memory:
        ok = _append_memory(name, args.memory)
        print(f"MEMORY.md: {'добавлена запись' if ok else 'ОТСУТСТВУЕТ — пропуск'}")
    else:
        print("MEMORY.md: нет новых знаний (--memory не задан)")
    st_changed = _update_state(name, args)
    print(f"STATE.md (машинный блок): {', '.join(st_changed) if st_changed else 'без изменений'}")
    return 0


# ------------------------------------------------------------ handoff --------

def cmd_handoff(args) -> int:
    frm = (args.frm or detect_identity()[0] or "—").upper()
    record = (
        f"FROM:       {frm}\n"
        f"TO:         {args.to.upper()}\n"
        f"TASK:       {args.task}\n"
        f"STATUS:     {args.status}\n"
        f"BLOCKERS:   {args.blockers}\n"
        f"FILES:      {args.files}\n"
        f"NEXT STEP:  {args.next}\n"
        f"TIMESTAMP:  {now_utc()}"
    )
    print("=== HANDOFF ===")
    print(record)
    if args.append:
        tasks = os.path.join(ROOT, "docs", "TASKS.md")
        text = read_text(tasks)
        if text is None:
            print("\ndocs/TASKS.md отсутствует — запись не добавлена.")
            return 1
        row = f"| {args.task} | handoff {frm}→{args.to.upper()} | {args.to.upper()} | {args.status} | {frm} | {datetime.date.today().isoformat()} | — |\n"
        with open(tasks, "a", encoding="utf-8") as fh:
            fh.write(row)
        print("\ndocs/TASKS.md: строка добавлена.")
    return 0


# -------------------------------------------------------------- locks --------

def _read_lock_rows(text: str):
    """Вернуть (pre_lines, header_idx, rows, post_start) для таблицы блокировок."""
    lines = text.splitlines()
    hidx = None
    for i, line in enumerate(lines):
        if LOCK_HEADER_KEY in line and line.lstrip().startswith("|"):
            hidx = i
            break
    if hidx is None:
        return lines, None, [], None
    # строки таблицы: header, separator, затем data до первой не-|-строки
    j = hidx + 2
    rows = []
    while j < len(lines) and lines[j].lstrip().startswith("|"):
        rows.append(lines[j])
        j += 1
    return lines, hidx, rows, j


def _parse_lock_row(row: str):
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    return cells if len(cells) >= 5 else None


def _active_locks(rows):
    out = []
    for r in rows:
        c = _parse_lock_row(r)
        if not c:
            continue
        if c[0].startswith("_(") or c[0] in ("", "—"):
            continue
        out.append({"path": c[0], "owner": c[1], "status": c[2], "since": c[3], "task": c[4]})
    return out


def _write_locks(lines, hidx, post_start, active):
    placeholder = "| _(нет активных блокировок)_ | — | — | — | — |"
    if active:
        new_rows = [f"| {a['path']} | {a['owner']} | {a['status']} | {a['since']} | {a['task']} |" for a in active]
    else:
        new_rows = [placeholder]
    new_lines = lines[:hidx + 2] + new_rows + lines[post_start:]
    with open(LOCKS_FILE, "w", encoding="utf-8") as fh:
        fh.write("\n".join(new_lines) + "\n")


def cmd_locks(args) -> int:
    text = read_text(LOCKS_FILE)
    if text is None:
        print("docs/LOCKS.md отсутствует.")
        return 1
    _, hidx, rows, _ = _read_lock_rows(text)
    active = _active_locks(rows)
    if not active:
        print("Активных блокировок нет.")
    else:
        for a in active:
            print(f"{a['path']}  —  {a['owner']}  ({a['status']}, с {a['since']}, задача {a['task']})")
    return 0


def cmd_lock(args) -> int:
    name = (args.name or detect_identity()[0] or "—").upper()
    text = read_text(LOCKS_FILE)
    if text is None:
        print("docs/LOCKS.md отсутствует.")
        return 1
    lines, hidx, rows, post = _read_lock_rows(text)
    if hidx is None:
        print("Таблица блокировок не найдена в docs/LOCKS.md.")
        return 1
    active = _active_locks(rows)
    for a in active:
        if a["path"] == args.path and a["owner"] != name:
            print("FILE LOCKED")
            print(f"FILE:     {args.path}")
            print(f"OWNER:    {a['owner']}")
            print(f"SINCE:    {a['since']}")
            print("PROPOSAL: handoff — см. docs/HANDOFF.md")
            return 2
        if a["path"] == args.path and a["owner"] == name:
            print(f"Файл уже заблокирован вами: {args.path}")
            return 0
    active.append({"path": args.path, "owner": name, "status": "locked",
                   "since": now_utc(), "task": args.task or "—"})
    _write_locks(lines, hidx, post, active)
    print(f"LOCKED {args.path} ({name})")
    return 0


def cmd_unlock(args) -> int:
    name = (args.name or detect_identity()[0] or "—").upper()
    text = read_text(LOCKS_FILE)
    if text is None:
        print("docs/LOCKS.md отсутствует.")
        return 1
    lines, hidx, rows, post = _read_lock_rows(text)
    if hidx is None:
        print("Таблица блокировок не найдена.")
        return 1
    active = _active_locks(rows)
    kept = [a for a in active if not (a["path"] == args.path and a["owner"] == name)]
    if len(kept) == len(active):
        print(f"Блокировка не найдена: {args.path} ({name})")
        return 1
    _write_locks(lines, hidx, post, kept)
    print(f"UNLOCKED {args.path} ({name})")
    return 0


# --------------------------------------------------------------- cli ---------

def cmd_status(args) -> int:
    """Сводка по всем агентам из их SYNC.md."""
    print("=== LAB STATUS ===")
    any_found = False
    for a in AGENTS:
        sync = parse_sync_table(read_text(os.path.join(ROOT, "agents", a, "SYNC.md")) or "")
        if not sync:
            print(f"\n[{a}] SYNC.md отсутствует или пуст")
            continue
        any_found = True
        print(f"\n[{a}]")
        print(f"  MISSION:   {sync.get('Текущая миссия', '—')}")
        print(f"  LAST:      {sync.get('Последняя завершённая задача', '—')}")
        print(f"  NEXT:      {sync.get('Следующий шаг', '—')}")
        print(f"  BLOCKERS:  {sync.get('Известные блокеры', '—')}")
        print(f"  UPDATED:   {sync.get('Время последнего обновления', '—')}")
    return 0 if any_found else 1


def _parse_tasks(text: str):
    """Строки очереди TASKS.md -> список dict."""
    cols = ["ID", "Задача", "Владелец", "Статус", "Передана кому", "Обновлено", "PR"]
    rows = []
    for line in text.splitlines():
        m = re.match(r"^\|(.+)\|\s*$", line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if len(cells) != len(cols):
            continue
        if cells[0] in ("ID", "") or set(cells[0]) <= set("-: "):
            continue
        rows.append(dict(zip(cols, cells)))
    return rows


def cmd_tasks(args) -> int:
    text = read_text(os.path.join(ROOT, "docs", "TASKS.md"))
    if text is None:
        print("docs/TASKS.md отсутствует.")
        return 1
    rows = _parse_tasks(text)
    if args.mine:
        rows = [r for r in rows if r["Владелец"].upper() == args.mine.upper()]
    if args.owner:
        rows = [r for r in rows if r["Владелец"].upper() == args.owner.upper()]
    if args.status:
        rows = [r for r in rows if r["Статус"].lower() == args.status.lower()]
    if not rows:
        print("Задач по фильтру нет.")
        return 0
    for r in rows:
        print(f"{r['ID']}  [{r['Статус']}]  {r['Владелец']}  — {r['Задача']}  (PR {r['PR']})")
    return 0


def _tasks_table_bounds(lines):
    """Индексы (header, last_row) таблицы очереди в TASKS.md."""
    h = None
    for i, l in enumerate(lines):
        if l.lstrip().startswith("|") and "ID" in l and "Задача" in l:
            h = i
            break
    if h is None:
        return None, None
    j = h + 2
    last = j - 1
    while j < len(lines) and lines[j].lstrip().startswith("|"):
        last = j
        j += 1
    return h, last


def cmd_task(args) -> int:
    path = os.path.join(ROOT, "docs", "TASKS.md")
    text = read_text(path)
    if text is None:
        print("docs/TASKS.md отсутствует.")
        return 1
    lines = text.splitlines()
    h, last = _tasks_table_bounds(lines)
    if h is None:
        print("Таблица очереди не найдена в TASKS.md.")
        return 1
    today = datetime.date.today().isoformat()
    if args.action == "add":
        owner = (args.owner or detect_identity()[0] or "—").upper()
        row = f"| {args.id} | {args.title} | {owner} | {args.status} | — | {today} | {args.pr or '—'} |"
        lines.insert(last + 1, row)
        print(f"TASKS.md: добавлена {args.id} [{args.status}] {owner}")
    else:  # set
        found = False
        for i in range(h + 2, last + 1):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if len(cells) == 7 and cells[0] == args.id:
                if args.status:
                    cells[3] = args.status
                if args.pr:
                    cells[6] = args.pr
                cells[5] = today
                lines[i] = "| " + " | ".join(cells) + " |"
                found = True
                print(f"TASKS.md: {args.id} → статус={cells[3]} pr={cells[6]}")
                break
        if not found:
            print(f"TASKS.md: задача {args.id} не найдена.")
            return 1
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + ("\n" if text.endswith("\n") else ""))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Agent automation engine — RED TEAM lab")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("boot", help="AGENT BOOT + STARTUP REPORT")
    b.add_argument("--name")
    b.set_defaults(fn=cmd_boot)

    c = sub.add_parser("checkpoint", help="AUTO SAVE: обновить SYNC/MEMORY")
    c.add_argument("--name")
    c.add_argument("--last", default="")
    c.add_argument("--next", default="")
    c.add_argument("--blockers", default="")
    c.add_argument("--memory", default="")
    c.add_argument("--commit", default="")
    c.add_argument("--branch", default="")
    c.add_argument("--pr", default="")
    c.add_argument("--status", default="", help="STATE: статус (машинно)")
    c.add_argument("--active", default="", help="STATE: активная задача (машинно)")
    c.set_defaults(fn=cmd_checkpoint)

    h = sub.add_parser("handoff", help="HANDOFF: сформировать запись")
    h.add_argument("--from", dest="frm")
    h.add_argument("--to", required=True)
    h.add_argument("--task", required=True)
    h.add_argument("--status", default="active")
    h.add_argument("--blockers", default="нет")
    h.add_argument("--files", default="—")
    h.add_argument("--next", required=True)
    h.add_argument("--append", action="store_true", help="добавить строку в docs/TASKS.md")
    h.set_defaults(fn=cmd_handoff)

    lk = sub.add_parser("lock", help="FILE LOCK: заблокировать файл")
    lk.add_argument("path")
    lk.add_argument("--name")
    lk.add_argument("--task", default="")
    lk.set_defaults(fn=cmd_lock)

    ul = sub.add_parser("unlock", help="снять блокировку")
    ul.add_argument("path")
    ul.add_argument("--name")
    ul.set_defaults(fn=cmd_unlock)

    ls = sub.add_parser("locks", help="показать активные блокировки")
    ls.set_defaults(fn=cmd_locks)

    st = sub.add_parser("status", help="сводка по всем агентам из SYNC.md")
    st.set_defaults(fn=cmd_status)

    tk = sub.add_parser("tasks", help="очередь задач из TASKS.md с фильтрами")
    tk.add_argument("--mine", help="задачи указанного агента")
    tk.add_argument("--owner", help="фильтр по владельцу")
    tk.add_argument("--status", help="фильтр по статусу (pending/active/blocked/done)")
    tk.set_defaults(fn=cmd_tasks)

    ta = sub.add_parser("task", help="вести очередь TASKS.md (add/set)")
    ta.add_argument("action", choices=["add", "set"])
    ta.add_argument("--id", required=True)
    ta.add_argument("--title", default="")
    ta.add_argument("--owner", default="")
    ta.add_argument("--status", default="pending")
    ta.add_argument("--pr", default="")
    ta.set_defaults(fn=cmd_task)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
