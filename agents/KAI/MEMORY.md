# KAI — память

Постоянная память KAI между сессиями. Здесь фиксируются только **проверенные факты**
и устойчивые выводы, полезные в будущих задачах. Сохранённые сведения не доказывают
текущее состояние среды — их нужно подтверждать заново в начале сессии.

Правила файла:
- не хранить секреты (см. [SECURITY.md](../../SECURITY.md));
- записывать факты с датой проверки;
- различать закреплённую идентичность и наблюдаемое состояние среды;
- не записывать роли других сотрудников и не менять свою роль без команды оператора.

## Закреплённая идентичность

- Имя: **KAI**. Роль: **Mobile Field Engineer**. Визуальный узел: **FIELD**.
- Дом: **Xiaomi 23053RN02Y**; среда **Android → Termux → Ubuntu/proot → Claude Code**.
- Рабочая зона: Xiaomi, Android, Termux, Ubuntu/proot.
- Ветки: `kai/<task>`. Оператор: **xnode**.
- Источник идентичности: [AGENTS.md](../../AGENTS.md), [agents/KAI/ROLE.md](ROLE.md), [TEAM.md](../../TEAM.md).

## Проверенные факты среды

- 2026-10-06 — среда выполнения подтверждена как `Linux PRoot-Distro`, Ubuntu, архитектура `aarch64`, инструмент **Claude Code**. Соответствует стеку KAI (Termux → Ubuntu/proot → Claude Code), а не ORBIT (Codex Cloud).

## Уроки и заметки

- 2026-10-06 — для `git push` по HTTPS в этой среде нужен настроенный credential helper: `gh auth setup-git` (после `gh auth login`). Без него push падает с `could not read Username for 'https://github.com'`.
- Рабочая база: GitHub repository **Xnode-sh/RED-TEAM-LAB**; процесс — [WORKFLOW.md](../../WORKFLOW.md) (PLAN → ISSUE → BRANCH → WORK → TEST → PR → REVIEW → MERGE). `main` — только проверенное состояние.

## История задач

- 2026-10-06 — инициализация постоянной памяти KAI: создан этот файл `agents/KAI/MEMORY.md` (ветка `kai/kai-memory-init`).
