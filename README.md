# glance

> One ClawHub skill that scaffolds any personal tracker you can describe.
> Dashboard, cron, reminders, mood, diary — from one sentence.

## Install

```bash
clawhub install glance
```

That's it. Tell your agent what you want to track.

## Example

```
You: "I want to track my daily workouts and build a reading habit"

Agent: "I'll create:
  workout — type, duration, notes (daily 9pm)
  reading — book title, pages read (daily 10pm)
  Dashboard shows both. Sound good?"

You: "Perfect, go ahead"

Agent: [scaffolds both → migrations → cron → dashboard built]
```

## CLI

```
glance setup               Minimal init (migrations)
glance list                 Your trackers
glance scaffold --name X   Create a new tracker
glance dashboard build      Build dashboard
glance dashboard open       Build and open
glance doctor               Health check
```

## Examples

See `examples/` for reference blueprints:
- mood, reminder, mit, diary_logger

## License

MIT
