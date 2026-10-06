#!/usr/bin/env python3
"""Pre-PR validation for RED └•TEAM•┐ lab™.

Проверяет перед Pull Request:
  1) отсутствие маркеров merge-конфликта;
  2) отсутствие секретов;
  3) валидность относительных ссылок в Markdown;
  4) целостность ролей инженеров;
  5) целостность протокола старта (Context Recovery).

Запуск:  python3 scripts/validate_pr.py
Код возврата 0 — все проверки пройдены; 1 — есть нарушения.
Документация механизма: docs/COLLABORATION.md.
"""
from __future__ import annotations
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS = ["RIG", "KAI", "NOVA", "ORBIT"]
AGENT_FILES = ["ROLE.md", "STATE.md", "MEMORY.md", "SYNC.md"]
SKIP_DIRS = {".git"}

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][^\"'\n]{8,}[\"']"),
]
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def walk(exts=None):
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if exts and os.path.splitext(name)[1] not in exts:
                continue
            yield os.path.join(base, name)


def rel(path):
    return os.path.relpath(path, ROOT)


def check_conflicts():
    bad = []
    for path in walk():
        try:
            with open(path, encoding="utf-8") as fh:
                for ln, line in enumerate(fh, 1):
                    if line.startswith("<<<<<<< ") or line.startswith(">>>>>>> ") or line.rstrip("\n") == "=======":
                        # '=======' учитывается только если файл несёт и стартовый маркер
                        if line.startswith("<<<<<<< ") or line.startswith(">>>>>>> "):
                            bad.append(f"{rel(path)}:{ln}")
        except (UnicodeDecodeError, IsADirectoryError):
            continue
    return bad


def check_secrets():
    bad = []
    for path in walk():
        try:
            with open(path, encoding="utf-8") as fh:
                for ln, line in enumerate(fh, 1):
                    for pat in SECRET_PATTERNS:
                        if pat.search(line):
                            bad.append(f"{rel(path)}:{ln}")
                            break
        except (UnicodeDecodeError, IsADirectoryError):
            continue
    return bad


def check_links():
    bad = []
    for path in walk(exts={".md"}):
        base = os.path.dirname(path)
        try:
            with open(path, encoding="utf-8") as fh:
                for ln, line in enumerate(fh, 1):
                    for m in LINK_RE.finditer(line):
                        target = m.group(1).split("#")[0].strip()
                        if not target or target.startswith(("http://", "https://", "mailto:")):
                            continue
                        if not os.path.exists(os.path.normpath(os.path.join(base, target))):
                            bad.append(f"{rel(path)}:{ln} -> {target}")
        except UnicodeDecodeError:
            continue
    return bad


def check_roles():
    bad = []
    for a in AGENTS:
        for f in AGENT_FILES:
            p = os.path.join(ROOT, "agents", a, f)
            if not os.path.isfile(p) or os.path.getsize(p) == 0:
                bad.append(f"agents/{a}/{f} отсутствует или пуст")
        role = os.path.join(ROOT, "agents", a, "ROLE.md")
        if os.path.isfile(role):
            with open(role, encoding="utf-8") as fh:
                if a not in fh.read():
                    bad.append(f"agents/{a}/ROLE.md не содержит имени {a}")
    return bad


def check_startup():
    bad = []
    p = os.path.join(ROOT, "AGENTS.md")
    if not os.path.isfile(p):
        return ["AGENTS.md отсутствует"]
    text = open(p, encoding="utf-8").read()
    for token in ["ROLE.md", "STATE.md", "MEMORY.md", "SYNC.md"]:
        if token not in text:
            bad.append(f"AGENTS.md не упоминает {token} в протоколе старта")
    return bad


def check_abs_links():
    """Внутренние Markdown-ссылки должны быть относительными (без ведущего '/')."""
    bad = []
    for path in walk(exts={".md"}):
        try:
            with open(path, encoding="utf-8") as fh:
                for ln, line in enumerate(fh, 1):
                    for m in LINK_RE.finditer(line):
                        target = m.group(1).strip()
                        if target.startswith("/"):
                            bad.append(f"{rel(path)}:{ln} -> {target}")
        except UnicodeDecodeError:
            continue
    return bad


def check_duplicate_headings():
    """Повтор одинакового заголовка внутри одного Markdown-файла."""
    bad = []
    for path in walk(exts={".md"}):
        seen, dup = set(), set()
        try:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    m = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
                    if not m:
                        continue
                    key = m.group(1).strip().lower()
                    if key in seen:
                        dup.add(m.group(1).strip())
                    seen.add(key)
        except UnicodeDecodeError:
            continue
        for d in sorted(dup):
            bad.append(f"{rel(path)}: повтор заголовка «{d}»")
    return bad


def advisory_markdown_lint():
    """Совещательный markdown lint (не блокирует): табы, хвостовые пробелы, финальный перевод строки."""
    warn = []
    for path in walk(exts={".md"}):
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except UnicodeDecodeError:
            continue
        for ln, line in enumerate(text.splitlines(), 1):
            if "\t" in line:
                warn.append(f"{rel(path)}:{ln} таб")
            if line.rstrip("\n") != line.rstrip():
                warn.append(f"{rel(path)}:{ln} хвостовой пробел")
        if text and not text.endswith("\n"):
            warn.append(f"{rel(path)} нет финального перевода строки")
    return warn


def git_diff_summary():
    import subprocess
    try:
        out = subprocess.run(["git", "diff", "--stat", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, timeout=30)
        return (out.stdout or out.stderr or "").strip()
    except Exception as exc:  # noqa: BLE001
        return f"(git diff недоступен: {exc})"


def main():
    checks = [
        ("merge-конфликты", check_conflicts),
        ("секреты", check_secrets),
        ("broken links", check_links),
        ("relative links", check_abs_links),
        ("duplicate headings", check_duplicate_headings),
        ("роли", check_roles),
        ("протокол старта", check_startup),
    ]
    failed = 0
    for title, fn in checks:
        problems = fn()
        if problems:
            failed += 1
            print(f"[FAIL] {title}: {len(problems)}")
            for item in problems:
                print(f"       - {item}")
        else:
            print(f"[ OK ] {title}")

    # Совещательные проверки (markdown lint) — не влияют на код возврата.
    warn = advisory_markdown_lint()
    if warn:
        print(f"[WARN] markdown lint: {len(warn)} (совещательно)")
        for item in warn[:20]:
            print(f"       - {item}")
    else:
        print("[ OK ] markdown lint")

    print("\n--- git diff summary (HEAD) ---")
    print(git_diff_summary() or "(нет изменений относительно HEAD)")

    if failed:
        print(f"\nВалидация не пройдена: проблемных проверок — {failed}.")
        return 1
    print("\nВалидация пройдена: блокирующие проверки OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
