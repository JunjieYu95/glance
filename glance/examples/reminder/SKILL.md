---
name: glance-reminder
description: Add, complete, and list reminders. Morning digest via cron.
---
## Usage

```bash
glance reminder add --title "renew passport" --due 2026-06-01
glance reminder done --id 3
glance reminder list
glance reminder digest
glance reminder stats
```

## Scripts

**scripts/log.py**
```
--add              Add a new reminder
--title TEXT       Required. What to remember.
--due DATE         Optional. Due date (YYYY-MM-DD).
--done             Mark reminder as done
--id INT           Reminder ID
--list             List all active reminders
```

**scripts/digest.py** — returns markdown digest for morning cron prompt.

**scripts/stats.py** — returns JSON for dashboard panel.

## Fields

- `title` (TEXT) — reminder text
- `due_date` (DATE) — optional deadline
- `done` (INTEGER) — 0=pending, 1=done
- `created_at` (TIMESTAMP)

## Cron

Schedule: `25 8 * * *` — 8:25 AM daily.
Notification: digest of today's reminders.
