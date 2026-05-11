# Glancely

> **Intent-first personal tracking. Describe what you want to track — your assistant handles the rest.**

Glancely is an [OpenClaw](https://openclaw.ai) skill that replaces app interfaces with natural conversation. Log workouts, track moods, set reminders, scaffold new habits — all by talking to your assistant. A read-only dashboard renders the results for a quick glance. No buttons, no forms, no clicks.

---

## The Practice of Simplism: You Don't Need 10 Apps for Simple Things

When app development becomes easier and cheaper, the instinct is to create more apps for every small need. But many personal workflows are structurally simple: record something, query it later, view a trend, edit a record. The core task is not complicated — what often makes it feel complicated is the rendering layer placed around it.

Once something becomes an app, we naturally add buttons, forms, dropdowns, tabs, filters, categories, and settings. Some are necessary. Some are visually pleasing. But many are extra steps between intent and action.

**This is the separation that matters:** what task do you really want to accomplish, and what interface is merely being rendered in front of that task?

When a large language model has access to the right tools and database, it can translate fuzzy requests into structured operations — writing records, querying data, summarizing patterns, generating visualisations — without forcing the user through a predefined UI path. In that setup, the button is no longer the product. The product is the operation behind the button.

Glancely practices this mindset. Instead of opening an app to log something, you talk to your assistant. The assistant extracts the relevant structure and saves it into a local SQLite database on your server. Later, if you want to query, view a trend, or generate an overview, you ask again.

There is a dashboard, but it is intentionally read-only. It is not another control centre. It is there for a quick glance — hence the name. For the right person, displaying it on a bedroom TV or secondary monitor means the information is just quietly present when needed.

**The deeper point is not about replacing ten apps with one.** That still keeps the app as the centre of the mental model. The more interesting shift is moving from interface-first to intent-first:

1. A unified way to express intent.
2. An assistant that operates the underlying system.
3. A minimal rendering layer only when something needs to be seen.

Maybe the future is not "an app for everything." Maybe it is fewer interfaces between intent and action.

---

## Status

> **Early development — not yet a fully polished MVP.** Core scaffolding, logging, and dashboard rendering work. Visual polish, rich overviews, and reminders integration are in progress. This project is being actively developed and shared early to invite feedback and collaboration.

---

## Install

```bash
# 1. Install the skill from ClawHub
openclaw skills install glancely

# 2. Install the Python package
pip3 install glancely
# On macOS Homebrew (PEP 668):
brew install pipx && pipx install glancely

# 3. One-time setup
glancely setup
```

---

## Usage

```
You: "I want to track my daily workouts and build a reading habit"

Agent: "I'll create:
  workout — type, duration, notes (daily 9pm)
  reading — book title, pages read (daily 10pm)
  Dashboard shows both. Sound good?"

You: "Perfect, go ahead"

Agent: [scaffolds both → migrations → cron → dashboard built]
```

---

## CLI

```
glancely setup               Minimal init (migrations)
glancely list                 Your trackers
glancely scaffold --name X   Create a new tracker
glancely dashboard build      Build dashboard
glancely dashboard open       Build and open in browser
glancely doctor               Health check
```

---

## Contributing

Contributions are warmly welcomed. This project is in active development and there is plenty of room to shape the direction. Whether you want to improve the dashboard, add new chart types, refine the scaffolding engine, or suggest a design idea — feel free to open an issue or pull request.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and [docs/DEVLOG.md](docs/DEVLOG.md) for the current development roadmap.

---

## License

MIT
