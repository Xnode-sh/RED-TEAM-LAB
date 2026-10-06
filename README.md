<p align="center"><img src="assets/rig-banner.svg" width="1280" alt="XNODE — RED └•TEAM•┐ lab™"></p>

[Штаб лаборатории](https://github.com/Xnode-sh/RED-TEAM-LAB) · [Профиль XNODE](https://github.com/Xnode-sh)

# RED └•TEAM•┐ lab™

Рабочий репозиторий команды XNODE для инструментов, мобильной автоматизации и системных проектов.

Оператор: **xnode**. GitHub: [Xnode-sh/RED-TEAM-LAB](https://github.com/Xnode-sh/RED-TEAM-LAB).

## Команда

| Узел | Роль | Дом |
| --- | --- | --- |
| [RIG — SYSTEM](agents/RIG/ROLE.md) | Systems & Linux Environment Engineer | Acer Aspire E1-570G / Debian 13 |
| [KAI — FIELD](agents/KAI/ROLE.md) | Mobile Field Engineer | Xiaomi 23053RN02Y / Termux → Ubuntu/proot → Claude Code |
| [NOVA — TOOLING](agents/NOVA/ROLE.md) | Mobile Automation & Tooling Engineer | Motorola Edge 2022 / native Termux → Codex CLI |
| [ORBIT — CLOUD / INTEGRATION](agents/ORBIT/ROLE.md) | Cloud Operations & Integration Engineer | Codex Cloud / ChatGPT Work |

## Архитектура лаборатории

![Четыре узла: RIG — SYSTEM, KAI — FIELD, NOVA — TOOLING, ORBIT — CLOUD / INTEGRATION](assets/team-architecture.svg)

Узлы работают в своих инженерных зонах и используют общий репозиторий. ORBIT координирует Issues и Pull Requests, проверяет целостность результатов и интеграцию через review. Облачная координация не меняет роли и полномочия RIG, KAI и NOVA.

[Дома и ответственность](TEAM.md) · [Процесс интеграции](WORKFLOW.md) · [Выбор идентичности](AGENTS.md)

## Работа

PLAN → ISSUE → BRANCH → WORK → TEST → PR → REVIEW → MERGE

`main` содержит только проверенное состояние. Рабочие ветки: `rig/<task>`, `kai/<task>`, `nova/<task>`, `orbit/<task>`.

## Структура

- `agents/` — закреплённые роли и состояние участников.
- `tools/` — инструменты и скрипты.
- `docs/` — документация.
- `reports/` — отчёты о выполненной работе и проверках.
- `projects/` — отдельные проекты и модули.
- `.github/` — шаблоны задач и pull request.

Правила: [TEAM.md](TEAM.md), [WORKFLOW.md](WORKFLOW.md), [SECURITY.md](SECURITY.md).
Выбор идентичности по среде: [AGENTS.md](AGENTS.md). Облачная роль: [ORBIT](agents/ORBIT/ROLE.md); локальная NOVA сохранена.

<img src="assets/rig-divider.svg" width="1280" alt="">

## Инженерный процесс лаборатории

`PLAN → ISSUE → BRANCH → WORK → TEST → PR → REVIEW → MERGE`

Команда: **RIG / KAI / NOVA / ORBIT**. NODE — фирменный маскот. [Правила работы](https://github.com/Xnode-sh/RED-TEAM-LAB/blob/main/WORKFLOW.md).
