# Personal Routine

One openclaw skill bundle that puts everything you'd otherwise need ten apps
for — diary, mood, reminders, daily MIT, and any tracker you want to invent —
behind a single read-only dashboard. Logging happens in chat. Notifications
happen via openclaw cron. Adding a brand-new tracker is one command.

## Why

You don't need a separate app for "track water," "track coffee," "log my
mood," "remind me about X." You need one place that holds them all and a
fast way to add new ones. This is that.

## Design philosophy

1. **Everything in one place.** One repo, one SQLite file, one dashboard,
   one chat surface.
2. **Read-only dashboard.** No interactive UI. Logging and queries happen
   through chat. The dashboard exists to be glanced at.
3. **Adding a new tracker is one command.** The `scaffold_component` skill
   creates the folder, generates the skill, runs migrations, registers the
   cron, and rebuilds the dashboard — all from one chat invocation.
4. **A component is a folder.** No central registry to edit. Drop a folder
   under `skills/` with a `component.toml` and it's wired in.

## What's included

| Component | What it does | Cron |
|---|---|---|
| `diary_logger` | Time-tracked activities → your Google Calendar | — |
| `mood` | Hourly mood check-in via chat | hourly 8–23 |
| `reminder` | Add/complete reminders + morning digest | 08:25 daily |
| `mit` | Most Important Task nightly check-in | 23:00 daily |
| `scaffold_component` | The meta-skill — create a new tracker | — |

## Install

```bash
git clone https://github.com/<you>/glance
cd glance
./install.sh
```

The installer will:
1. Install Python deps.
2. Apply per-component SQL migrations into `~/.glance/data.db`.
3. Ask for your openclaw cron config (agent_id, session_target, session_key).
4. Run the Google OAuth flow for Calendar (you bring your own OAuth client).
5. Tell you to create a Calendar named "Glance Diary".
6. Build the dashboard.

## Add a new tracker

In chat:

> "I want to start tracking my coffee intake — 2 fields, shots and notes."

The `scaffold_component` skill picks this up and runs:

```bash
./glance/skills/scaffold_component/scripts/scaffold.py \
  --name coffee_intake --title "Coffee" \
  --field shots:int --field notes:text \
  --cron "0 9 * * *" --notify "How much coffee today?"
```

That generates `skills/coffee_intake/` with a working `log.py`, `stats.py`,
migrations, and (if `--cron` is set) registers an openclaw cron task. The
next dashboard build shows a Coffee panel.

## Component contract

See [`docs/component-contract.md`](docs/component-contract.md). Every
component is just a folder with `component.toml` + `migrations/*.sql` +
`scripts/log.py` + `scripts/stats.py`. That's it.

## Bring your own Google OAuth client

The repo never ships a shared OAuth client (avoids Google verification +
keeps the maintainer off the hook for your tokens). You create a Desktop
OAuth client in Google Cloud Console, download `credentials.json`, drop it
at `~/.glance/credentials.json`, and run install.

## License

MIT — see `LICENSE`.
