---
name: scaffold_component
description: Create a new tracking component end-to-end. Triggered when the user says "I want to track <X>", "add a new component", "scaffold a new tracker", "新增一个 <X> 记录", or any request to start tracking something not already covered.
---

# Scaffold Component

The meta-skill. Creates a new tracking component (folder + skill + migrations +
dashboard panel + optional cron) in one shot. **No central file edits required**
— the new component is wired in by virtue of existing on disk.

## When to invoke

User says any of:
- "I want to start tracking my coffee intake"
- "add a sleep tracker"
- "scaffold a new component called <X>"
- "新增一个 <X> 记录器"

## What it does

1. Asks for: `name` (snake_case folder name), `title` (panel title), optional
   `cron_schedule` + `notification_text`, optional `fields` (list of typed
   columns the user wants to record).
2. Copies `templates/component/` → `glance/skills/<name>/`.
3. Substitutes `{{name}}`, `{{title}}`, `{{fields_sql}}` in the template.
4. Runs `core.storage.migrations.apply_component_migrations` for the new
   component → tables exist in `~/.glance/data.db`.
5. If `cron_schedule` is set, registers an openclaw cron task pointing at
   `skills/<name>/scripts/notify.py`.
6. Triggers a dashboard rebuild so the new panel appears.

## Examples

```bash
./scripts/scaffold.py \
  --name coffee_intake \
  --title "Coffee" \
  --field "shots:int" \
  --field "notes:text" \
  --cron "0 9 * * *" \
  --notify "How much coffee did you have?"
```

After this runs, the user can immediately say "log coffee 2 shots" and the
new component handles it, AND the next dashboard build shows a Coffee panel.

## Files emitted

```
skills/<name>/
├── component.toml
├── SKILL.md
├── migrations/001_init.sql       # CREATE TABLE <name>_entries (...)
├── scripts/
│   ├── log.py                    # generic field-driven logger
│   ├── stats.py                  # generic count + recent rows
│   └── notify.py                 # only if cron was set
└── tests/test_smoke.py
```
