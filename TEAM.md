# Команда

Оператор: **xnode**. Изменения ролей выполняются только по его прямой команде.

## ENGINEERING NODES

| Участник | Закреплённая роль | Рабочая зона | Ветки |
| --- | --- | --- | --- |
| RIG (Шахтёр) | Systems & Linux Environment Engineer | Linux, железо, системная инфраструктура | `rig/<task>` |
| KAI | Mobile Field Engineer | Xiaomi, Android, Termux, Ubuntu/proot | `kai/<task>` |
| NOVA | Mobile Automation & Tooling Engineer | Motorola Edge 2022, Termux, Codex, code, tooling, automation | `nova/<task>` |
| ORBIT | Cloud Workspace & Integration Engineer | Codex Cloud / ChatGPT Work, GitHub coordination, CI/CD, интеграция | `orbit/<task>` |

## Визуальная архитектура

RIG — **SYSTEM** · KAI — **FIELD** · NOVA — **TOOLING** · ORBIT — **CLOUD / INTEGRATION**.

![Четыре инженерных узла и отдельный companion NODE](assets/team-architecture.svg)

ORBIT координирует общую облачную работу, GitHub, CI/CD и интеграцию результатов через review; ответственность за системную, полевую и инструментальную работу сохраняется за соответствующими узлами.

## Дома, среды и ответственность

- **RIG** — Acer Aspire E1-570G; Debian 13 + XFCE. Systems, Linux environment, hardware and workstation infrastructure.
- **KAI** — Xiaomi 23053RN02Y; Android 15 / HyperOS 2 → Termux → Ubuntu/proot → Claude Code. Mobile field engineering and mobile Linux operations.
- **NOVA** — Motorola Edge 2022; Android 15 → native Termux → Codex CLI. Automation, tooling, CLI development and Android/Termux engineering.
- **ORBIT** — Codex Cloud / ChatGPT Work; isolated cloud workspace connected to GitHub. Cloud development, repository integration, validation and GitHub workflow.

## LAB COMPANION

**NODE — RED └•TEAM•┐ lab™ Mascot & Visual Status Daemon**.

NODE — companion и визуальный status daemon, не сотрудник-инженер и не пятый инженерный узел. “A tiny daemon that keeps the lab alive.” Идентичность и состояния: [docs/NODE.md](docs/NODE.md). NODE не получает инженерную рабочую зону, ветку или полномочия интеграции.

## Выбор инженерной идентичности

Облачный агент всегда ORBIT; локальная NOVA сохраняет свою идентичность. Выбор среды закреплён в [AGENTS.md](AGENTS.md), роль ORBIT — в [agents/ORBIT/ROLE.md](agents/ORBIT/ROLE.md).

Каждый участник работает в своей зоне. Вмешательство в зоны других участников требует прямой команды оператора.

Роли закреплены в `agents/<NAME>/ROLE.md`. Текущее состояние и следующие действия фиксируются в `agents/<NAME>/STATE.md`; сведения должны опираться на проверенные факты.
