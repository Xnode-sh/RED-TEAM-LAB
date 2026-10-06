# Automation (движок автоматизации)

Превращает документированные протоколы [системы совместной работы](COLLABORATION.md)
в исполняемые инструменты. Движок **автоматизирует** существующую систему и ничего
в ней не меняет: роли, архитектура и документы остаются прежними.

Весь движок — в [scripts/agent.py](../scripts/agent.py) и
[scripts/validate_pr.py](../scripts/validate_pr.py). Скрытых механизмов нет.

## Команды

| Этап | Команда | Что делает |
| --- | --- | --- |
| 1, 2, 7 | `python3 scripts/agent.py boot [--name NAME]` | AGENT BOOT: читает AGENTS.md, определяет личность, читает ROLE/STATE/MEMORY/SYNC (без падения при отсутствии) и печатает STARTUP REPORT |
| 3 | `python3 scripts/agent.py checkpoint --last "…" --next "…" [--memory "…"]` | AUTO SAVE: обновляет SYNC.md (и при `--memory` добавляет запись в MEMORY.md) без дублей |
| 4 | `python3 scripts/agent.py handoff --to NAME --task T-xxx --next "…" [--append]` | HANDOFF: печатает запись стандартного формата и (с `--append`) добавляет строку в TASKS.md |
| 5 | `python3 scripts/agent.py lock <path>` / `unlock <path>` / `locks` | FILE LOCK: реестр блокировок в LOCKS.md; при чужой блокировке печатает `FILE LOCKED` и возвращает код 2 |
| 6 | `python3 scripts/validate_pr.py` | AUTO VALIDATION: конфликты, секреты, broken/relative links, duplicate headings, роли, протокол старта + markdown lint (совещательно) и git diff summary |
| — | `python3 scripts/agent.py status` | Сводка по всем агентам (миссия/последняя задача/следующий шаг/блокеры/обновлено) из их SYNC.md |
| — | `python3 scripts/agent.py tasks [--mine NAME] [--owner NAME] [--status S]` | Очередь задач из TASKS.md с фильтрами |
| — | `python3 scripts/agent.py task add --id T-xxx --title "…" [--owner N] [--status S] [--pr …]` | Добавить задачу в очередь TASKS.md |
| — | `python3 scripts/agent.py task set --id T-xxx [--status S] [--pr …]` | Обновить статус/PR задачи в очереди |

`checkpoint` теперь обновляет и машинный блок `STATE.md` (`STATE:BEGIN..STATE:END`),
не трогая прозу: поля `--status` и `--active` пишутся в этот блок автоматически.

Автозапуск валидатора перед commit — хук [scripts/hooks/pre-commit](../scripts/hooks/pre-commit):
`git config core.hooksPath scripts/hooks`.

## Архитектура

```
агент активирован
   │
   ▼
scripts/agent.py boot ──> AGENTS.md ─> ROLE ─> STATE ─> MEMORY ─> SYNC
   │                         (отсутствующий файл → предупреждение, не падение)
   ▼
STARTUP REPORT  (STATUS/ROLE/MISSION/CURRENT TASK/LAST ACTION/LAST UPDATE/BLOCKERS/FILES READ/NEXT STEP)
   │
   ├── работа в своей зоне ── lock/unlock (LOCKS.md) ── handoff (TASKS.md, HANDOFF.md)
   │
   ▼
scripts/validate_pr.py  (перед commit; хук pre-commit)
   │
   ▼
checkpoint ──> SYNC.md (+ MEMORY.md)   [STATE.md — вручную, формат варьируется]
```

## Что теперь автоматически

- Единый запуск любого инженера и чтение контекста с устойчивостью к отсутствующим файлам.
- Единый STARTUP REPORT из фактического содержимого файлов (без ручного набора).
- Формирование записи HANDOFF и добавление её в очередь задач.
- Блокировка/разблокировка файлов и проверка занятости (`FILE LOCKED`).
- Полный набор проверок перед commit (через hook) и в CI (при наличии scope `workflow`).
- Обновление SYNC.md и MEMORY.md контрольной точкой.

## Что остаётся ручным

- Определение личности в нераспознанной среде (движок не присваивает чужую личность — по AGENTS.md).
- Обновление `STATE.md` (формат у инженеров разный; автозапись могла бы повредить историю).
- Содержательные решения: что передать, что считать знанием, когда объявлять `BLOCKER`.
- Реальный merge в `main` — только оператор после review.

## Предложения по следующему этапу

1. ~~Машинно-читаемый раздел `STATE.md`~~ — ✅ блок `STATE:BEGIN..STATE:END`, пишется `agent.py checkpoint`.
2. ~~CI-workflow `validate.yml`~~ — ✅ (PR #10).
3. ~~Индекс очереди задач~~ — ✅ `agent.py tasks` (фильтры) и `agent.py task add/set` (ведение).
4. ~~Команда `agent.py status`~~ — ✅.
5. Автогенерация записи в TASKS.md при открытии PR — частично: есть `agent.py task add` (ручной/хук); остаётся привязка к событию PR.
