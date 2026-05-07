---
name: diary_logger
description: Log time-tracked activities to your Google Calendar. Triggered when the user says "log diary", "log <activity>", "记录日志", or any direct mention of recording time/activities.
---

# Diary Logger

Logs activities as events on a dedicated Google Calendar (e.g. "Personal Routine
Diary"). Computes per-category statistics for the dashboard.

## When to invoke

- "log diary"
- "log <activity> from 2:30pm to 4pm"
- "log <activity> till 4pm"
- "log <activity> at 10am"
- "记录日志 ..."

## Time handling

Four patterns, all handled by `scripts/log.py`:

| Pattern             | Example                          | Resolution                              |
|---------------------|----------------------------------|-----------------------------------------|
| Both explicit       | `from 2:30pm to 4pm`             | Parse both, write event                 |
| Start only          | `from 4pm`                       | Start = parsed, end = now               |
| End only            | `till 2:15pm`                    | Start = last event end, end = parsed    |
| No explicit time    | (no time tokens)                 | Start = last event end, end = now       |

## Categories

`prod` (default), `admin`, `nonprod`. Override via `--category`.

## Examples

```bash
./scripts/log.py --title "wrapper refactor" --start "2:30pm" --end "4:00pm" --category prod
./scripts/log.py --title "quick lunch till 2:15pm" --category admin
./scripts/log.py --title "answer messages"
```

## Stats output

`scripts/stats.py` returns `{today_count, total_minutes, by_category, recent}`.
