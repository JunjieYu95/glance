#!/usr/bin/env python3
"""Build the read-only dashboard HTML.

Walk skills/, call each component's scripts/stats.py as a subprocess (each
component owns its imports), aggregate into one static HTML page.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from glancely.core.registry import discover_components  # noqa: E402
from glancely.core.storage import apply_all_migrations  # noqa: E402
from glancely.dashboard.charts import render_chart  # noqa: E402
from glancely.dashboard.overview import render_overview_panel  # noqa: E402

SKILLS_ROOT = REPO_ROOT / "glancely" / "skills"
TEMPLATE_PATH = Path(__file__).resolve().parent / "template.html"


def _run_stats(component) -> dict:
    if not component.stats_script.is_file():
        return {"status": "error", "summary": {"error": "missing scripts/stats.py"}, "rows": []}
    try:
        out = subprocess.check_output(
            [sys.executable, str(component.stats_script)],
            cwd=REPO_ROOT,
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
            timeout=30,
            stderr=subprocess.PIPE,
        )
        return json.loads(out)
    except subprocess.TimeoutExpired:
        return {"status": "error", "summary": {"error": "stats.py timed out"}, "rows": []}
    except subprocess.CalledProcessError as exc:
        return {
            "status": "error",
            "summary": {"error": exc.stderr.decode("utf-8", "replace")[:500]},
            "rows": [],
        }
    except json.JSONDecodeError as exc:
        return {
            "status": "error",
            "summary": {"error": f"stats.py emitted non-JSON: {exc}"},
            "rows": [],
        }


def _status_badge(status: str, freshness_hours: float | None, threshold: float | None) -> str:
    if status == "error":
        return '<span class="badge bad">error</span>'
    if status == "empty":
        return '<span class="badge muted">empty</span>'
    if threshold is not None and freshness_hours is not None and freshness_hours > threshold:
        return f'<span class="badge bad">stale {freshness_hours:.1f}h</span>'
    if freshness_hours is not None:
        return f'<span class="badge ok">fresh {freshness_hours:.1f}h</span>'
    return '<span class="badge ok">ok</span>'


def _render_summary(summary: dict) -> str:
    if not summary:
        return ""
    items = []
    for k, v in summary.items():
        if isinstance(v, dict):
            inner = ", ".join(
                f"{html.escape(str(ik))}: {html.escape(str(iv))}" for ik, iv in v.items()
            )
            items.append(f"<div><strong>{html.escape(str(k))}</strong>: {inner}</div>")
        else:
            items.append(
                f"<div><strong>{html.escape(str(k))}</strong>: {html.escape(str(v))}</div>"
            )
    return "\n".join(items)


def _render_rows(rows: list[dict]) -> str:
    if not rows:
        return '<div class="muted-row">no recent entries</div>'
    keys: list[str] = []
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    head = "".join(f"<th>{html.escape(k)}</th>" for k in keys)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(r.get(k, '')))}</td>" for k in keys) + "</tr>"
        for r in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _render_reminder_panel(payload: dict) -> str:
    """Render reminder component as a grouped sidebar panel."""
    import html as html_mod
    rows = payload.get("rows", [])
    if not rows:
        return ""

    # Group reminders by bucket
    groups: dict[str, list[dict]] = {"overdue": [], "today": [], "soon": [], "later": [], "unscheduled": []}
    bucket_labels = {"overdue": "Overdue", "today": "Today", "soon": "Soon", "later": "Later", "unscheduled": "Unscheduled"}
    now_iso = __import__("datetime").datetime.now().isoformat()

    for r in rows:
        due = r.get("due_date")
        if due and due <= now_iso and r.get("status") != "done":
            groups["overdue"].append(r)
        elif due and due[:10] == now_iso[:10]:
            groups["today"].append(r)
        elif due:
            groups["later"].append(r)
        else:
            groups["unscheduled"].append(r)

    html_parts = ['<section class="panel reminder-panel"><header><h2>Reminders</h2></header>']
    for bucket, items in groups.items():
        if not items:
            continue
        count = len(items)
        html_parts.append(
            f'<div class="reminder-group {bucket}">'
            f'<div class="reminder-group-head">{bucket_labels[bucket]}'
            f'<span class="count">{count}</span></div>'
        )
        for item in items:
            title = html_mod.escape(str(item.get("title", "")))
            due_str = item.get("due_date", "")[:10] if item.get("due_date") else ""
            html_parts.append(
                f'<div class="reminder-item {bucket}">'
                f'<span class="reminder-title">{title}</span>'
                f'<span class="reminder-due">{due_str}</span>'
                f'</div>'
            )
        html_parts.append('</div>')
    html_parts.append('</section>')
    return "\n".join(html_parts)


def _render_panel(component, payload: dict) -> str:
    badge = _status_badge(
        payload.get("status", "ok"),
        payload.get("freshness_hours"),
        component.freshness_hours,
    )

    chart_config = component.chart_config
    if chart_config and chart_config.get("chart", {}).get("type"):
        # Render as chart panel
        chart_type = chart_config["chart"]["type"]
        chart_title = chart_config["chart"].get("title", component.title)
        chart_html = render_chart(chart_type, payload, chart_config)

        # Still show summary data below chart if rows exist
        rows_html = _render_rows(payload.get("rows") or [])
        summary_html = _render_summary(payload.get("summary") or {})

        return f"""
<section class="panel" data-component="{html.escape(component.name)}">
  <header>
    <h2>{html.escape(chart_title)}</h2>
    {badge}
  </header>
  <div class="chart-container">{chart_html}</div>
  {f'<div class="summary">{summary_html}</div>' if summary_html else ""}
  {f"<details><summary>Recent</summary>{rows_html}</details>" if payload.get("rows") else ""}
</section>
""".strip()
    else:
        # Backward-compatible basic card (unchanged)
        summary_html = _render_summary(payload.get("summary") or {})
        rows_html = _render_rows(payload.get("rows") or [])
        return f"""
<section class="panel" data-component="{html.escape(component.name)}">
  <header>
    <h2>{html.escape(component.title)}</h2>
    {badge}
  </header>
  <div class="summary">{summary_html}</div>
  <details><summary>Recent</summary>{rows_html}</details>
</section>
""".strip()


DEFAULT_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>glancely &mdash; Dashboard</title>
  <style>
    :root {
      --bg: #050814;
      --panel: rgba(10, 18, 32, 0.88);
      --panel-2: rgba(13, 28, 47, 0.92);
      --ink: #e5f4ff;
      --muted: #8aa2b8;
      --line: rgba(125, 211, 252, 0.18);
      --green: #2dd4bf;
      --amber: #f59e0b;
      --rose: #fb7185;
      --blue: #38bdf8;
      --violet: #a78bfa;
      --shadow: 0 18px 42px rgba(0, 0, 0, 0.36);
      --glow: 0 0 24px rgba(56, 189, 248, 0.16);
      --ok: #2dd4bf;
      --bad: #fb7185;
      --chart-line: rgba(125, 211, 252, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background:
        radial-gradient(circle at 20% -10%, rgba(56, 189, 248, 0.16), transparent 32%),
        radial-gradient(circle at 86% 0%, rgba(167, 139, 250, 0.13), transparent 28%),
        linear-gradient(180deg, #050814 0%, #08111f 44%, #050814 100%);
      color: var(--ink);
      font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(125, 211, 252, 0.055) 1px, transparent 1px),
        linear-gradient(90deg, rgba(125, 211, 252, 0.055) 1px, transparent 1px);
      background-size: 28px 28px;
      mask-image: linear-gradient(to bottom, rgba(0,0,0,0.65), transparent 76%);
      z-index: 0;
    }

    /* ── Header ── */
    .dashboard-header {
      padding: 12px 20px 8px;
      border-bottom: 1px solid var(--line);
      background: rgba(5, 8, 20, 0.82);
      position: sticky;
      top: 0;
      z-index: 5;
      backdrop-filter: blur(12px);
    }
    .header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .header-row h1 { margin: 0; font-size: 18px; letter-spacing: 0; }
    .header-meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px;
      color: var(--muted);
      font-size: 12px;
      margin-top: 2px;
    }
    .meta-sep { opacity: 0.5; }
    .refresh-button {
      border: 1px solid var(--line);
      background: rgba(56, 189, 248, 0.08);
      color: var(--ink);
      border-radius: 6px;
      padding: 6px 10px;
      font: inherit;
      font-size: 12px;
      cursor: pointer;
    }
    .refresh-button:hover {
      border-color: var(--blue);
      color: var(--blue);
    }

    /* ── Main Grid ── */
    main {
      padding: 10px 16px 18px;
      display: grid;
      gap: 10px;
      position: relative;
      z-index: 1;
    }
    /* Dashboard grid with sidebar */
    .dashboard-grid {
      display: grid;
      grid-template-columns: 7fr 3fr;
      gap: 10px;
      align-items: start;
    }
    .dashboard-main {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 10px;
    }
    .dashboard-sidebar {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    @media (max-width: 768px) {
      .dashboard-grid {
        grid-template-columns: 1fr;
      }
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
      gap: 10px;
    }
    .grid-top {
      display: grid;
      grid-template-columns: minmax(0, 7fr) minmax(280px, 3fr);
      gap: 10px;
    }

    /* ── Panels ── */
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      box-shadow: var(--shadow);
      padding: 10px 12px;
      overflow: hidden;
      position: relative;
      backdrop-filter: blur(12px);
    }
    .panel::before {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      border-top: 1px solid rgba(125, 211, 252, 0.22);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.03), var(--glow);
    }
    .panel header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 8px;
    }
    .panel h2 { margin: 0; font-size: 15px; letter-spacing: 0; }
    .summary div { margin: 2px 0; color: var(--ink); }

    /* ── Badges ── */
    .badge {
      font-size: 11px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      padding: 3px 9px;
      border-radius: 999px;
      border: 1px solid var(--line);
      color: var(--muted);
      background: rgba(15, 23, 42, 0.9);
      white-space: nowrap;
    }
    .badge.ok {
      color: #99f6e4;
      background: rgba(45, 212, 191, 0.12);
      border-color: rgba(45, 212, 191, 0.38);
    }
    .badge.bad {
      color: #fda4af;
      background: rgba(251, 113, 133, 0.12);
      border-color: rgba(251, 113, 133, 0.42);
    }
    .badge.muted {
      color: var(--muted);
      background: rgba(15, 23, 42, 0.9);
      border-color: var(--line);
    }

    details { margin-top: 8px; }
    details summary { cursor: pointer; color: var(--muted); }
    table {
      width: 100%; border-collapse: collapse;
      font-size: 12px; margin-top: 8px;
    }
    th, td {
      text-align: left; padding: 4px 6px;
      border-bottom: 1px solid var(--line);
    }
    th { color: var(--muted); font-weight: 500; }
    .muted-row { color: var(--muted); font-size: 12px; padding: 4px 0; }
    .chart-empty {
      color: var(--muted); font-size: 13px;
      text-align: center; padding: 24px 0;
    }

    /* ── Overview Panel ── */
    .overview-panel {
      grid-column: 1 / -1;
    }
    .overview-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 8px;
    }
    .ov-card {
      flex: 1 1 130px;
      min-width: 110px;
      padding: 10px;
      border-radius: 6px;
      background: var(--panel-2);
      border: 1px solid var(--line);
      text-align: center;
    }
    .ov-label {
      display: block;
      font-size: 10px;
      color: var(--muted);
      margin-bottom: 4px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .ov-value {
      display: block;
      font-size: 18px;
      font-weight: 650;
      margin-top: 4px;
    }
    .ov-badge-value { font-size: 14px; font-weight: 600; }
    .ov-sparkline svg { margin: 2px 0; }
    .ov-progress .ov-value { font-size: 14px; margin-top: 2px; }

    /* ── Overview Grid (matches reference dashboard) ── */
    .overview {
      display: grid;
      grid-template-columns: 56px repeat(var(--ov-days, 14), minmax(0, 1fr));
      gap: 3px;
      align-items: center;
    }
    .overview .row-label {
      font-size: 10px;
      color: var(--muted);
      text-align: right;
      padding-right: 6px;
    }
    .overview .day-label {
      font-size: 10px;
      color: var(--muted);
      text-align: center;
      line-height: 1.1;
    }
    .overview .mood-cell {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 18px;
    }
    .overview .mood-dot { border-radius: 50%; }
    .overview .prod-cell {
      height: 38px;
      display: flex;
      align-items: flex-end;
      justify-content: center;
    }
    .overview .prod-bar {
      width: 70%;
      min-height: 1px;
      background: var(--green);
      border-radius: 2px 2px 0 0;
    }
    .overview .prod-num {
      font-size: 10px;
      color: var(--muted);
      text-align: center;
    }
    .overview .mit-cell {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 18px;
    }
    .overview .mit-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }
    .overview .mit-dot.done { background: var(--green); }
    .overview .mit-dot.open { background: var(--rose); }
    .overview .mit-dot.absent {
      background: transparent;
      border: 1px dashed var(--line);
    }

    /* ── Progress Bar ── */
    .chart-progress { margin: 8px 0; }
    .progress-label { font-size: 12px; color: var(--muted); display: block; margin-bottom: 4px; }
    .progress-track {
      height: 10px;
      background: rgba(8, 13, 25, 0.9);
      border: 1px solid var(--line);
      border-radius: 5px;
      overflow: hidden;
      margin: 4px 0;
    }
    .progress-fill {
      height: 100%;
      border-radius: 5px;
    }
    .progress-value {
      font-size: 12px;
      color: var(--muted);
      display: block;
      text-align: right;
    }

    /* ── Status Card ── */
    .chart-status-card { text-align: center; padding: 16px 0; }
    .status-title { font-size: 12px; color: var(--muted); margin-bottom: 4px; }
    .status-value { font-size: 16px; font-weight: 600; margin-bottom: 8px; }

    /* ── Bar Chart ── */
    .chart-bars { margin: 8px 0; }
    .bar-item {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 4px 0;
    }
    .bar-label {
      font-size: 12px;
      min-width: 60px;
      text-align: right;
      color: var(--muted);
    }
    .bar-track {
      flex: 1;
      height: 16px;
      background: rgba(8, 13, 25, 0.9);
      border: 1px solid var(--line);
      border-radius: 4px;
      overflow: hidden;
    }
    .bar-fill {
      height: 100%;
      border-radius: 4px;
      min-width: 2px;
    }
    .bar-value {
      font-size: 12px;
      min-width: 36px;
      color: var(--ink);
      text-align: left;
    }

    /* ── Pie / Donut ── */
    .chart-pie-wrapper, .chart-donut-wrapper {
      text-align: center;
      margin: 8px 0;
    }
    .chart-pie, .chart-donut { display: inline-block; }
    .pie-slice-hit { cursor: pointer; }
    .donut-center-text {
      font-size: 18px;
      font-weight: 600;
      fill: var(--ink);
    }
    .chart-legend {
      list-style: none;
      padding: 0;
      margin: 8px 0 0;
      display: flex;
      flex-wrap: wrap;
      gap: 6px 14px;
      justify-content: center;
      font-size: 12px;
    }
    .legend-swatch {
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 2px;
      margin-right: 4px;
      vertical-align: middle;
    }

    /* ── Sparkline ── */
    .chart-sparkline { display: inline-block; vertical-align: middle; }

    /* ── Heatmap ── */
    .chart-heatmap {
      display: inline-block;
      margin: 8px 0;
      overflow-x: auto;
      max-width: 100%;
    }
    .hm-header-row {
      display: flex;
      gap: 2px;
      margin-bottom: 2px;
      padding-left: 24px;
    }
    .hm-header {
      width: 14px;
      font-size: 9px;
      color: var(--muted);
      text-align: center;
    }
    .hm-row { display: flex; gap: 2px; margin: 1px 0; }
    .hm-cell {
      width: 14px;
      height: 14px;
      border-radius: 2px;
      position: relative;
    }
    .hm-cell:hover { outline: 2px solid var(--ink); z-index: 1; }
    .hm-empty { background: transparent; }

    /* ── Calendar Grid ── */
    .chart-calendar-grid { margin: 8px 0; }
    .cal-month { margin-bottom: 12px; }
    .cal-month-title {
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 4px;
    }
    .cal-dow-row, .cal-grid {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 2px;
      max-width: 280px;
    }
    .cal-dow {
      font-size: 10px;
      color: var(--muted);
      text-align: center;
      padding: 2px 0;
    }
    .cal-cell {
      aspect-ratio: 1;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
      cursor: default;
    }
    .cal-empty, .cal-future { background: transparent; }
    .cal-no-data { background: var(--line); opacity: 0.3; }
    .cal-future { color: var(--muted); opacity: 0.3; }
    .cal-day { font-size: 10px; }

    /* ── Timeline ── */
    .chart-timeline {
      position: relative;
      margin: 8px 0;
      padding-left: 24px;
    }
    .chart-timeline::before {
      content: "";
      position: absolute;
      left: 8px;
      top: 4px;
      bottom: 4px;
      width: 2px;
      background: var(--line);
    }
    .timeline-item {
      position: relative;
      margin-bottom: 12px;
    }
    .timeline-dot {
      position: absolute;
      left: -20px;
      top: 5px;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--green);
      border: 2px solid var(--panel);
    }
    .timeline-time {
      font-size: 11px;
      color: var(--muted);
      margin-bottom: 2px;
    }
    .timeline-title { font-size: 13px; font-weight: 500; }
    .timeline-desc { font-size: 12px; color: var(--muted); }

    /* ── Reminder Panel (sidebar) ── */
    .reminder-group { display: grid; gap: 6px; }
    .reminder-group-head {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
      margin-top: 10px;
    }
    .reminder-group-head:first-child { margin-top: 0; }
    .reminder-group-head .count {
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 0 8px;
      line-height: 18px;
    }
    .reminder-group.overdue .reminder-group-head { color: var(--rose); }
    .reminder-group.today .reminder-group-head { color: var(--amber); }
    .reminder-group.soon .reminder-group-head { color: var(--amber); }
    .reminder-group.later .reminder-group-head { color: var(--blue); }
    .reminder-group.unscheduled .reminder-group-head { color: var(--muted); }
    .reminder-item {
      border-left: 3px solid var(--line);
      padding: 4px 8px;
      background: var(--panel-2);
      border-radius: 4px;
      font-size: 12px;
    }
    .reminder-item.overdue { border-left-color: var(--rose); background: rgba(251, 113, 133, 0.1); }
    .reminder-item.today { border-left-color: var(--amber); background: rgba(245, 158, 11, 0.1); }
    .reminder-item.soon { border-left-color: var(--amber); }
    .reminder-item.later { border-left-color: var(--blue); }
    .reminder-item.unscheduled { border-left-color: rgba(209, 209, 204, 0.5); }
    .reminder-item .reminder-due {
      font-size: 11px;
      color: var(--muted);
      margin-top: 2px;
    }
    .reminder-item .reminder-title { font-weight: 500; }

    /* ── MIT Stats Row ── */
    .mit-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 8px;
      margin-bottom: 10px;
    }
    .mit-stat {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 6px 10px;
      background: var(--panel-2);
    }
    .mit-stat .stat-num {
      font-size: 20px;
      font-weight: 650;
      line-height: 1.15;
    }
    .mit-stat .stat-num.good { color: var(--green); }
    .mit-stat .stat-num.warn { color: var(--amber); }
    .mit-stat .stat-num.bad { color: var(--rose); }
    .mit-stat .stat-label {
      color: var(--muted);
      font-size: 10px;
      margin-top: 2px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .mit-strip {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
      gap: 6px;
    }
    .mit-day {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 6px 8px;
      font-size: 11px;
      background: var(--panel-2);
    }
    .mit-day.done {
      border-color: rgba(45,212,191,0.38);
      background: rgba(45,212,191,0.09);
    }
    .mit-day.open {
      border-color: rgba(251,113,133,0.34);
      background: rgba(251,113,133,0.1);
    }
    .mit-day .date {
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 3px;
    }

    /* ── Chart Container ── */
    .chart-container { margin-top: 4px; }

    /* ── Responsive ── */
    @media (max-width: 980px) {
      .dashboard-header, main { padding-left: 14px; padding-right: 14px; }
      .grid-top { grid-template-columns: 1fr; }
    }
    @media (max-width: 640px) {
      .dashboard-header { padding: 8px 10px 6px; }
      .header-row { flex-direction: column; align-items: flex-start; gap: 4px; }
      h1 { font-size: 16px; }
      h2 { font-size: 14px; }
      main { padding: 8px 10px 14px; gap: 8px; }
      .panel { padding: 8px 10px; }
      .mit-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
      .mit-stat .stat-num { font-size: 16px; }
      .mit-strip { grid-template-columns: repeat(auto-fill, minmax(86px, 1fr)); }
    }
  </style>
</head>
<body>
  <header class="dashboard-header">
    <div class="header-row">
      <div>
        <h1>glancely</h1>
        <div class="header-meta">
          <span>Built {built_at}</span>
        </div>
      </div>
      <button class="refresh-button" onclick="location.reload()">Refresh</button>
    </div>
  </header>
  <main>
    <div class="grid">{panels}</div>
  </main>
</body>
</html>
"""


def _render_reminders_from_db() -> str:
    """Read reminders directly from the DB and render as a sidebar panel."""
    import html as html_mod
    try:
        from glancely.core.storage import get_connection
        conn = get_connection()
        rows = [dict(r) for r in conn.execute(
            "SELECT title, due_date, status FROM reminders WHERE status != 'done' ORDER BY due_date ASC NULLS LAST"
        ).fetchall()]
        conn.close()
    except Exception:
        return ""

    if not rows:
        return ""

    groups = {"today": [], "soon": [], "later": [], "unscheduled": []}
    from datetime import date
    today = date.today().isoformat()
    for r in rows:
        due = r.get("due_date", "")
        if due and str(due)[:10] == today:
            groups["today"].append(r)
        elif due and str(due)[:10] <= (date.today().__str__()):
            groups["soon"].append(r)
        elif due:
            groups["later"].append(r)
        else:
            groups["unscheduled"].append(r)

    labels = {"today": "Today", "soon": "Overdue", "later": "Later", "unscheduled": "Unscheduled"}
    colors = {"today": "amber", "soon": "rose", "later": "blue", "unscheduled": "muted"}

    html_parts = ['<section class="panel reminder-panel"><div class="panel-head"><h2>Reminders</h2></div>']
    for bucket in ["today", "soon", "later", "unscheduled"]:
        items = groups[bucket]
        if not items:
            continue
        html_parts.append(f'<div class="reminder-group {bucket}">'
                         f'<div class="reminder-group-head">{labels[bucket]}'
                         f'<span class="count">{len(items)}</span></div>')
        for item in items:
            title = html_mod.escape(str(item.get("title", "")))
            due_str = str(item.get("due_date", ""))[:10] if item.get("due_date") else ""
            html_parts.append(f'<div class="reminder-item {bucket}">'
                             f'<span class="reminder-title">{title}</span>'
                             f'<span class="reminder-due">{due_str}</span></div>')
        html_parts.append('</div>')
    html_parts.append('</section>')
    return "\n".join(html_parts)


def build(output_path: Path | None = None, run_migrations: bool = True) -> dict:
    from glancely.core.storage.db import GLANCE_HOME

    if output_path is None:
        output_path = GLANCE_HOME / "dashboard" / "index.html"

    if run_migrations:
        apply_all_migrations(SKILLS_ROOT)

    components = discover_components(panel_only=True)

    panels_html: list[str] = []
    reminder_html: str = ""
    statuses: dict[str, str] = {}
    overview_meta: list[dict] = []  # NEW: collect for overview panel

    for comp in components:
        payload = _run_stats(comp)
        statuses[comp.name] = payload.get("status", "unknown")

        # Render reminder component as sidebar
        if comp.name == "reminder":
            reminder_html = _render_reminder_panel(payload)
        else:
            panels_html.append(_render_panel(comp, payload))

        # Collect overview metadata if chart_config exists with overview section
        chart_config = comp.chart_config
        if chart_config and chart_config.get("overview", {}).get("enabled") is not False:
            overview_meta.append(
                {
                    "name": comp.name,
                    "title": comp.title,
                    "overview": chart_config["overview"],
                    "payload": payload,
                }
            )

    # Render overview panel
    overview_html = render_overview_panel(overview_meta)

    # Insert overview before the grid, reminder as sidebar
    if overview_html:
        panels_html.insert(0, overview_html)

    # If no scaffolded reminder component, read reminders directly from DB
    if not reminder_html:
        reminder_html = _render_reminders_from_db()

    # Always use dashboard grid layout for full-width display
    main_html = '\n'.join(panels_html)
    if reminder_html:
        body_content = f'<div class="dashboard-grid"><div class="dashboard-main">{main_html}</div><aside class="dashboard-sidebar">{reminder_html}</aside></div>'
    else:
        body_content = f'<div class="dashboard-main" style="width:100%">{main_html}</div>'

    template = (
        TEMPLATE_PATH.read_text(encoding="utf-8") if TEMPLATE_PATH.is_file() else DEFAULT_TEMPLATE
    )
    html_out = template.replace("{built_at}", datetime.now().strftime("%Y-%m-%d %H:%M"))
    html_out = html_out.replace("{panels}", body_content)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_out, encoding="utf-8")
    return {
        "output": str(output_path),
        "components": list(statuses.keys()),
        "statuses": statuses,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=None)
    p.add_argument("--no-migrate", action="store_true")
    args = p.parse_args(argv)
    result = build(Path(args.out) if args.out else None, run_migrations=not args.no_migrate)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
