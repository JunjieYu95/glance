---
name: mit
description: Set or update the day's Most Important Task. Triggered when the user says "set MIT", "今天的 MIT", "tomorrow's MIT is X", or replies to the nightly check-in.
---

# MIT (Most Important Task)

One MIT per day. Nightly cron asks two questions; agent records both via
`log.py --upsert`.

## Examples

```bash
./scripts/log.py --upsert --date 2026-05-03 --task "ship draft" --completed true
./scripts/today_brief.py             # prints today's MIT for the cron prompt
```
