---
name: mood
description: Log a mood check-in reply. Triggered when the user replies to a mood question, or says "log mood", "记录心情", or shares how they feel.
---

# Mood

Hourly cron fires a question; user replies in the same chat session; agent
calls `log.py --raw "<reply>"`.

## Examples

```bash
./scripts/log.py --raw "还行，下午有点累"
./scripts/log.py --raw "great" --score 8 --label happy
```

Same-session matters: the cron that asks must be in the user's main session,
not isolated, so the reply lands with the asking agent.
