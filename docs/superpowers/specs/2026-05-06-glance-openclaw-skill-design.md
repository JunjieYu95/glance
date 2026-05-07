# glance v0.2.0 — OpenClaw Skill Redesign

**Date:** 2026-05-06
**Status:** Draft
**Author:** Junjie Yu

## Overview

Redesign glance as a professional, installable OpenClaw skill bundle via ClawHub.
Framework + example blueprints + scaffold generator that builds personalized
trackers from natural language intent. No hardcoded trackers. No mandatory
auth dependencies. Everything lives under `~/.glance/` for user data durability.

---

## 1. Architecture

```
glance/                          ← ClawHub skill root (immutable)
├── SKILL.md                     ← master handbook + dispatch table
├── install.sh
├── pyproject.toml
├── glance/                      ← core framework (the skeleton)
│   ├── cli.py                   ← single CLI entry point
│   ├── core/
│   │   ├── auth/                ← per-component auth dispatcher
│   │   ├── registry/            ← component discovery
│   │   ├── storage/             ← SQLite + migrations
│   │   └── cron.py              ← openclaw cron job management
│   ├── dashboard/               ← static HTML builder
│   └── skills/
│       └── scaffold_component/  ← meta-skill: create trackers from intent
└── examples/                    ← reference blueprints (never activated)
    ├── mood/
    │   ├── SKILL.md
    │   └── component.toml
    ├── reminder/
    │   ├── SKILL.md
    │   └── component.toml
    ├── mit/
    │   ├── SKILL.md
    │   └── component.toml
    └── diary_logger/
        ├── SKILL.md
        └── component.toml

~/.glance/                       ← user data (survives skill updates)
├── data.db                      ← shared SQLite
├── openclaw.toml                ← cron config (agent_id, session, etc.)
├── dashboard/
│   └── index.html               ← built dashboard
├── credentials/                 ← per-tracker auth tokens
│   └── diary_logger/
│       └── token.json
└── components/                  ← user-scaffolded trackers
    ├── workout/
    │   ├── component.toml
    │   ├── migrations/
    │   ├── scripts/
    │   └── SKILL.md
    └── reading/
        └── ...
```

### Key principles

- **Framework vs. content**: core handles infrastructure (CLI, cron, dashboard, migrations). Examples are reference blueprints, never auto-installed.
- **User data in ~/.glance/**: user-scaffolded trackers, auth tokens, and the database live outside the skill directory. Survives `clawhub update`.
- **No central registry**: discovery walks `~/.glance/components/` and `examples/`. Adding a tracker means dropping a folder.
- **Auth per tracker**: no global Google dependency. Each `component.toml` declares its own auth requirements.

---

## 2. SKILL.md Design

### 2.1 Master SKILL.md

The master SKILL.md is a **handbook + dispatch table**, not an exhaustive CLI reference.
Its job: analyze user intent, route to the correct sub-skill, and call the right script.

```yaml
---
name: glance
description: >
  Personal tracker framework. Dashboard, cron, reminders, mood, diary, MIT.
  Scaffold new trackers in one command from natural language.
version: 0.2.0
metadata:
  openclaw:
    requires:
      bins: [python3, pip]
    os: [macos, linux]
    install:
      - kind: pip
        package: glance
    envVars:
      - name: GLANCE_HOME
        required: false
        description: Custom data directory (default ~/.glance)
---
```

**Dispatch table:**

| User says             | Action                                                            |
|-----------------------|-------------------------------------------------------------------|
| "log mood"            | Check `~/.glance/components/mood/`. If exists → run log.py. If not → read `examples/mood/` for ref → scaffold first |
| "remind me" / "add"   | Check `~/.glance/components/reminder/`. Same fallback pattern     |
| "what's my MIT"       | Check `~/.glance/components/mit/`. Same fallback pattern          |
| "log diary" / "time"  | Check `~/.glance/components/diary/`. Same fallback pattern        |
| "build dashboard"     | Run `glance dashboard build`                                      |
| "create tracker for X"| Read `glance/skills/scaffold_component/SKILL.md` → infer → propose → scaffold |
| "track my habit"      | Same scaffold flow: infer fields, cron, notify → propose → confirm|

**Per-route workflow:**
1. Check if the user already has a matching component in `~/.glance/components/`
2. If yes: read its SKILL.md, call its scripts/log.py with user arguments
3. If no: read the matching example in `examples/` as a reference blueprint, then run the scaffold flow (intent → propose → confirm → scaffold)
4. Report the result

### 2.2 Example Blueprint SKILL.md (per-component)

Each example has its own SKILL.md, publishable independently on ClawHub:

```yaml
---
name: glance-mood
description: Hourly mood check-ins via chat
---
## Usage
glance mood log --raw "feeling great" --score 8
glance mood stats

## Scripts
scripts/log.py --raw "..." [--score 1-10]
scripts/stats.py  ← called by dashboard
```

### 2.3 Scaffold SKILL.md

Teaches the agent how to infer tracker structure from user intent:

```yaml
---
name: glance-scaffold
description: >
  Create new personal trackers from natural language. Infers field names,
  types, cron schedules, and notification text. Proposes a plan before
  making changes.
---
## Intent → Plan → Confirm → Scaffold

1. **Analyze** the user's goal. Infer:
   - Tracker name (snake_case)
   - Fields (name:type pairs)
   - Cron schedule (when should they be prompted?)
   - Notification text

2. **Propose** a plan listing trackers, fields, and cron before touching anything.
   Ask for confirmation.

3. **Scaffold** each confirmed tracker:
   glance scaffold --name <name> --field <name:type> ... --cron <expr> --notify <text>

4. **Dashboard** auto-builds after each scaffold.
```

---

## 3. Setup Flow

Setup is conversation-driven, not a questionnaire:

1. User installs: `clawhub install glance` → framework + example blueprints land on disk
2. User describes intent: *"I want to track my workouts and build a reading habit"*
3. Agent reads scaffold SKILL.md → infers structure → proposes a plan:
   > "I'll create 2 trackers: workout (type, duration, notes, 9pm daily) and reading (book, pages, 10pm daily). Dashboard shows both. Sound good?"
4. User confirms or revises
5. Agent runs `glance scaffold` for each → migrations, cron, dashboard auto-built
6. Auth prompted only if a tracker needs it (e.g., diary_logger → Google OAuth)

### CLI commands

```
glance setup [--skip-cron] [--skip-auth]    ← minimal framework init (migrations only)
glance doctor                                ← health check
glance list                                  ← discovered user components
glance scaffold --name X --field ... --cron ... --notify ...
glance dashboard build [--out PATH]
glance dashboard open
glance version
```

### Cron configuration

Cron config lives in `~/.glance/openclaw.toml`:
```toml
agent_id = "ceo_secretary"
session_target = "main"
session_key = "agent:ceo_secretary:telegram:direct:<id>"
```

Prompted once, on first scaffold that includes `--cron`. If skipped, cron is deferred.

---

## 4. Component Contract

### 4.1 Folder shape

```
~/.glance/components/<name>/
├── component.toml         ← required
├── SKILL.md               ← optional, reusable on ClawHub
├── migrations/
│   └── 001_init.sql
├── scripts/
│   ├── log.py             ← entrypoint for logging
│   └── stats.py           ← dashboard payload as JSON
└── tests/
```

### 4.2 component.toml schema

```toml
[component]
name        = "workout"
title       = "Workout"
version     = "0.1.0"
description = "Track daily workouts."

[panel]
enabled  = true
order    = 10
freshness_hours = 24

[storage]
tables = ["workout_entries"]

[cron]
schedule    = "0 21 * * *"
command     = "python3 scripts/notify.py"
description = "Evening workout nudge"

[auth]                      ← NEW: per-component auth
kind = "none"               ← "none" | "google" | "env"
# For kind=google:
# kind = "google"
# required_env = ["GOOGLE_CREDENTIALS_JSON"]
# scopes = ["..."]
# For kind=env:
# kind = "env"
# required_env = ["MY_API_KEY"]
```

### 4.3 Script contracts

**stats.py** — outputs JSON on stdout:
```json
{
  "freshness_hours": 3.2,
  "status": "ok",
  "summary": { "today_count": 2, "total_minutes": 90 },
  "rows": [
    { "time": "08:30", "type": "run", "duration_minutes": 45 }
  ]
}
```

**log.py** — entrypoint for recording entries. Reads CLI flags. Writes to data.db or external service.

### 4.4 Migrations

- Live in `migrations/` directory, applied in lexicographic order
- Tracked in shared `_migrations(component, name, applied_at)` table
- Run automatically on: `glance setup`, `glance scaffold`, `glance dashboard build`

---

## 5. Dashboard

Static HTML, light/dark mode, responsive grid. Builds from `~/.glance/components/*/scripts/stats.py` (user trackers only). Dashboard is read-only. No interactive UI. Logging happens through chat.

---

## 6. Testing Strategy

| Layer | What | How |
|---|---|---|
| Core framework | setup, doctor, list, migrations | pytest with temp `GLANCE_HOME` |
| Scaffold | end-to-end: folder, component.toml, migrations, cron | pytest + filesystem inspection |
| Dashboard | HTML builds, panels render, --no-migrate | pytest + HTML parsing |
| SKILL.md dispatch | Master routes intent correctly | Manual review + agent testing |
| Example blueprints | Each example's scripts work in isolation | pytest per example |
| CLI smoke | version, --help, subcommand --help | CI smoke step |

Target: ~25 tests total (up from 13 current). All runnable via `pytest glance/ -v`.
CI: Python 3.9, 3.10, 3.11, 3.12 on GitHub Actions.

---

## 7. Files to Create/Modify

### New files
- `SKILL.md` (master, at repo root)
- `examples/*/SKILL.md` (mood, reminder, mit, diary_logger)
- `glance/skills/scaffold_component/SKILL.md`
- `glance/core/auth/__init__.py` (auth dispatcher)
- `tests/` additions

### Modified files
- `pyproject.toml` — update version, package-data for examples/
- `glance/cli.py` — add `glance setup` as minimal init
- `glance/core/openclaw_cron.py` → rename to `cron.py`, simplify
- `glance/core/registry/discover.py` — search both `~/.glance/components/` and `examples/`
- `glance/core/storage/db.py` — `GLANCE_HOME` as data root
- `glance/dashboard/build.py` — build from both sources
- `install.sh` — simplify to pip install + glance setup
- `README.md` — update for ClawHub install flow

### Removed
- Hardcoded Google OAuth from `glance setup` (moved to per-tracker auth)
- `glance/core/auth/google_oauth.py` → moved to example diary_logger as an optional dep
