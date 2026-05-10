# Dashboard Polish — Remaining Tasks

> **Last updated:** 2026-05-10 (after v0.3.0 date-grid overhaul)
> **Context:** v0.3.0 shipped auto-inference (heatmap for numeric, calendar_grid for text) and updated mood/MIT examples. Core scaffolding and chart rendering work correctly. Visual quality and completeness still need work.

## Reference Dashboard

The target design is visible at `https://junjies-mac-mini.tail4a50bf.ts.net:18792/`. Key characteristics:

### Visual Design
- **Dark mode only** — deep navy background (#050814), subtle grid overlay, glass-morphism panels with `backdrop-filter: blur(12px)`
- CSS variables for theming: `--bg`, `--panel`, `--panel-2`, `--ink`, `--muted`, `--line`, `--green`, `--amber`, `--rose`, `--blue`, `--violet`
- Glow effects on panels (`--glow: 0 0 24px rgba(56, 189, 248, 0.16)`)
- Subtle radial gradient background
- Monospace-friendly font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- 28px grid lines overlay with mask-image fade at bottom

### Layout
- **Sticky header** with refresh button and status
- **Grid-based layout** with multiple grid variants:
  - `.grid-top` — main content (7fr) + right sidebar (3fr) for reminders/MIT
  - `.grid-2`, `.grid-3`, `.subgrid` — for flexible panel arrangements
- Panels have `border-radius: 6px`, `box-shadow`, and `border: 1px solid var(--line)`
- Built-at timestamp with `data-state-banner` class

### Component Panels (what the reference has that v0.3.0 lacks)

1. **Overview Panel** (spans full width)
   - Composite cards showing key signals from ALL trackers
   - Card types: `sparkline` (with inline SVG), `stat` (number + label), `badge` (colored pill), `progress` (bar)
   - v0.3.0 has a basic overview but lacks:
     - The sparkline card type with inline SVG rendering
     - Rich multi-card layout that spans all components
   - **STATUS:** exists in `dashboard/overview.py` but visual quality is basic

2. **Reminders Panel** (right sidebar)
   - Groups: overdue (rose), today (amber), soon (amber), later (blue), unscheduled
   - Each reminder has colored left border, title, due date
   - Count badges on group headers
   - v0.3.0 has `reminder` example but it's a standalone component, not integrated into the sidebar
   - **STATUS:** not integrated into dashboard layout

3. **MIT Panel** (Most Important Task)
   - Stats row: completion rate, completed 7d, logged 7d
   - Strip of MIT-day cards (auto-fill grid), each showing date + task + done/open status
   - Color-coded: green border = done, red border = open
   - v0.3.0: MIT changed to calendar_grid, which shows completion pattern but lacks the task detail + stats
   - **STATUS:** calendar_grid works but doesn't show task text or stats

4. **Diary Panel** (top-left, large)
   - Donut chart showing category breakdown (prod/admin/nonprod)
   - Weekly trend SVG line chart
   - Today's summary and comparison bars (today vs last week per category)
   - v0.3.0: diary_logger exists but uses Google Calendar auth — deferred
   - **STATUS:** deferred to next stage

5. **Mood Panel**
   - Horizontal bars with mood labels + counts
   - Color-coded swatches per mood type
   - Recent mood notes with left-border styling
   - v0.3.0: mood changed to calendar_grid (shows daily pattern)
   - **STATUS:** calendar_grid is good for glance, but bars + notes layout is richer

6. **Wake Up Chart**
   - SVG-based time chart (line/scatter over days)
   - Not in v0.3.0 at all
   - **STATUS:** not implemented

7. **Ideas Panel**
   - Grid of idea cards (auto-fill)
   - Not in v0.3.0
   - **STATUS:** not implemented

## Immediate Priorities (next agent should tackle)

### P1: Dark Mode Dashboard Template
**File:** `glancely/dashboard/build.py` (`DEFAULT_TEMPLATE` or `template.html`)
- Replace current light/dark media-query template with dark-mode-only CSS matching the reference
- Apply the color palette, glow effects, grid overlay, sticky header
- Use the same glass-morphism panel style
- **No JavaScript** — keep it pure CSS

### P2: Rich Overview Panel
**Files:** `glancely/dashboard/overview.py`, `glancely/dashboard/charts.py`
- Enhance `render_overview_panel` to produce `.overview-grid` with flex-wrap cards
- Each card should support: sparkline (SVG inline), stat (large number), badge, progress bar
- Overview should span full width at top of dashboard

### P3: Reminders Integration
**Files:** `glancely/examples/reminder/`, `glancely/dashboard/build.py`
- When reminder component exists, render its panel as a right-sidebar panel with grouped view
- Groups: overdue / today / soon / later
- Colored left borders, count badges, due dates

### P4: MIT Panel Enhancement
**Files:** `glancely/examples/mit/scripts/stats.py`, `glancely/examples/mit/chart.toml`
- Add stats row above calendar_grid: completion rate, completed 7d, logged 7d
- Ensure `today_brief.py` output is consumable by dashboard

## Lower Priority

### P5: Dashboard Layout Intelligence
**File:** `glancely/dashboard/build.py`
- Smart grid layout: place certain components (MIT, reminders) in right sidebar
- Overview always spans full width at top
- Diary (when implemented) gets large top-left panel
- Other components auto-fill remaining grid

### P6: Component-Specific Renderers
- Mood: calendar_grid + horizontal bars for mood distribution
- Reading: heatmap + donut chart for pages vs minutes ratio
- Coffee: calendar_grid + sparkline for last 7 days trend

### P7: Diary Panel (deferred)
- Google Calendar integration, donut charts, weekly trends
- See `glancely/examples/diary_logger/` for existing code

## v0.3.0 Completed

- [x] Auto-infer chart type: numeric → heatmap, text/bool → calendar_grid
- [x] Dynamic chart.toml template with `_presence` marker
- [x] Mood example: changed to calendar_grid
- [x] MIT example: changed to calendar_grid with 90-day window
- [x] Template import fix: `glance.core.storage` → `glancely.core.storage`
- [x] pip3/anyBins support in SKILL.md metadata
- [x] PEP 668 guidance in README and install.sh
- [x] Published to PyPI v0.3.0 and ClawHub

## Known Gaps

- `_presence` is added to all rows unconditionally (not just text trackers) — harmless but noisy
- `label_field` removed from chart.toml.tmpl — not consumed by current renderers, but needed for future mood-label-in-cells feature
- `date_field` hardcoded to `created_at` in scaffold template — MIT uses `date` field, requires manual config
- No integration tests for `build_mapping` output (`first_numeric`, `color_scheme`)
- `tests/test_scaffold.py` is at project root, not in `glancely/skills/scaffold_component/tests/` — outside default testpaths
