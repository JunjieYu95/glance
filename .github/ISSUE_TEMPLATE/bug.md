---
name: Bug report
about: Something doesn't work the way the README says it should
title: "[bug] "
labels: bug
---

## What happened

<!-- Plain description of the problem. One sentence is fine. -->

## What you expected

<!-- One sentence is fine. -->

## How to reproduce

<!--
Exact commands. Example:

```bash
glance setup
glance diary log --title "test" --start 2pm --end 3pm
```
-->

## `glance doctor` output

<!-- Run `glance doctor` and paste the JSON. Redact anything sensitive. -->

```json

```

## Environment

- glance version: <!-- run `glance version` -->
- Python version: <!-- run `python3 --version` -->
- OS: <!-- macOS / Linux / Windows + version -->
- openclaw cron config present (`~/.glance/openclaw.toml`): <!-- yes / no -->
- Google OAuth credentials present (`~/.glance/credentials.json`): <!-- yes / no -->
