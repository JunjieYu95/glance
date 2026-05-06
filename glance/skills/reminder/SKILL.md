---
name: reminder
description: Add, complete, and digest personal reminders. Triggered when the user says "remind me to X", "add reminder", "mark X done", "show reminders", "提醒我".
---

# Reminders

## Examples

```bash
./scripts/log.py --add --title "renew passport" --due 2026-06-01
./scripts/log.py --done --id 42
./scripts/log.py --list
./scripts/digest.py                 # markdown for chat / dashboard
```

Cron-triggered morning digest reads pending reminders and asks the agent to
forward the markdown to the user.
