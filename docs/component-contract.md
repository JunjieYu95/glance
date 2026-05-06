# Component Contract

Every tracking component (diary, mood, workout, …) is a self-contained folder
under `glance/skills/<name>/`. The dashboard, the scaffolder, and the
install script all rely on this contract — nothing else.

## Folder shape

```
skills/<name>/
├── component.toml         # required, see schema below
├── SKILL.md               # openclaw skill definition
├── scripts/
│   ├── log.py             # entrypoint for "log/record" actions
│   └── stats.py           # returns dashboard payload as JSON on stdout
├── migrations/
│   ├── 001_init.sql       # first migration; runs on install or scaffold
│   └── 00N_*.sql          # subsequent migrations, applied in lex order
├── tests/
└── references/            # optional skill references
```

A component is "registered" by **existing on disk**. There is no central
registry file to edit. The dashboard walks `skills/*/component.toml` at build
time.

## `component.toml` schema

```toml
[component]
name        = "diary_logger"          # must match folder name
title       = "Diary"                  # dashboard panel title
version     = "0.1.0"
description = "Time-tracked activities logged to Google Calendar."

[panel]
enabled  = true
order    = 10                          # lower = earlier in dashboard
freshness_hours = 24                   # red badge if no data within N hours

[storage]
# Tables this component owns inside the shared data.db.
# The migration runner asserts these exist after migrations apply.
tables = ["diary_entries"]

[cron]
# Optional. If present, install.sh registers an openclaw cron task that runs
# `command` on `schedule`. Cadence syntax = standard cron.
# Notifications belong here — components do NOT roll their own notifier.
schedule = "0 21 * * *"                # 9pm daily
command  = "python3 scripts/notify.py"
description = "Evening diary nudge"

[deps]
# Optional. Python packages this component needs. Aggregated by install.sh.
python = ["google-auth", "google-api-python-client"]
```

## Script contracts

### `scripts/log.py`

- Entrypoint for openclaw skill invocation.
- Reads structured args (CLI flags or `--input-json`).
- Returns JSON on stdout describing what was logged.
- Writes to either the shared `data.db` (component's own tables) or an
  external sink (e.g. Google Calendar for `diary_logger`).

### `scripts/stats.py`

- Called by the dashboard build at render time.
- Output: JSON on stdout, this exact shape:

```json
{
  "freshness_hours": 3.2,
  "status": "ok",                      // "ok" | "stale" | "error" | "empty"
  "summary": {                          // free-form, rendered by dashboard template
    "today_count": 5,
    "total_minutes": 312,
    "by_category": {"prod": 240, "admin": 72}
  },
  "rows": [                             // optional, last-N entries to show
    {"time": "14:30", "title": "wrapper refactor", "duration": 90}
  ]
}
```

- Reads-only. Never writes.
- Must succeed even if the component has zero data (return `status: "empty"`).

## Migrations

- Live in `skills/<name>/migrations/`.
- Filenames must sort lexicographically in apply order (`001_*`, `002_*`, …).
- Applied state tracked in a single shared table `_migrations(component, name, applied_at)`.
- Migration runner is in `core/storage/migrations.py`.
- Runs automatically: (a) on `install.sh`, (b) when `scaffold_component`
  creates a new component, (c) on every `dashboard/build.py` invocation
  (idempotent, cheap).

## Why this shape

- **Decentralized**: adding a component never edits a central file. Just drop
  the folder. This is what makes the scaffolder one-shot.
- **Read-only dashboard**: `stats.py` is the only contract the dashboard needs.
  Components can change their internals freely.
- **One DB**: queries can join across components later if we ever want to
  (e.g. correlate mood with workout) without orchestrating multiple files.
- **Cron via openclaw**: notifications, periodic syncs, and reminders are all
  just cron entries declared in `component.toml`.
