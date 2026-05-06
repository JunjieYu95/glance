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

from glance.core.registry import discover_components  # noqa: E402
from glance.core.storage import apply_all_migrations  # noqa: E402

SKILLS_ROOT = REPO_ROOT / "glance" / "skills"
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
        return {"status": "error", "summary": {"error": exc.stderr.decode("utf-8", "replace")[:500]}, "rows": []}
    except json.JSONDecodeError as exc:
        return {"status": "error", "summary": {"error": f"stats.py emitted non-JSON: {exc}"}, "rows": []}


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
            inner = ", ".join(f"{html.escape(str(ik))}: {html.escape(str(iv))}" for ik, iv in v.items())
            items.append(f"<div><strong>{html.escape(str(k))}</strong>: {inner}</div>")
        else:
            items.append(f"<div><strong>{html.escape(str(k))}</strong>: {html.escape(str(v))}</div>")
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


def _render_panel(component, payload: dict) -> str:
    badge = _status_badge(
        payload.get("status", "ok"),
        payload.get("freshness_hours"),
        component.freshness_hours,
    )
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


DEFAULT_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>glance — Dashboard</title>
  <style>
    :root { color-scheme: light dark; --bg:#fafafa; --fg:#222; --muted:#888; --card:#fff; --line:#eee; --ok:#4a7; --bad:#c44; }
    @media (prefers-color-scheme: dark) {
      :root { --bg:#111; --fg:#eee; --muted:#888; --card:#1a1a1a; --line:#2a2a2a; }
    }
    body { background:var(--bg); color:var(--fg); font:14px/1.5 -apple-system, system-ui, sans-serif; margin:0; padding:24px; }
    h1 { margin:0 0 4px; font-size:20px; }
    .built-at { color:var(--muted); font-size:12px; margin-bottom:24px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:16px; }
    .panel { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:16px; }
    .panel header { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:8px; }
    .panel h2 { margin:0; font-size:16px; }
    .summary div { margin:2px 0; }
    .badge { font-size:11px; padding:2px 8px; border-radius:4px; }
    .badge.ok { background:rgba(74,170,119,0.18); color:var(--ok); }
    .badge.bad { background:rgba(204,68,68,0.18); color:var(--bad); }
    .badge.muted { background:rgba(136,136,136,0.18); color:var(--muted); }
    details { margin-top:8px; }
    details summary { cursor:pointer; color:var(--muted); }
    table { width:100%; border-collapse:collapse; font-size:12px; margin-top:8px; }
    th, td { text-align:left; padding:4px 6px; border-bottom:1px solid var(--line); }
    th { color:var(--muted); font-weight:500; }
    .muted-row { color:var(--muted); font-size:12px; padding:4px 0; }
  </style>
</head>
<body>
  <h1>glance</h1>
  <div class="built-at">Built {built_at}</div>
  <div class="grid">{panels}</div>
</body>
</html>
"""


def build(output_path: Path, run_migrations: bool = True) -> dict:
    if run_migrations:
        apply_all_migrations(SKILLS_ROOT)

    components = [c for c in discover_components(SKILLS_ROOT, panel_only=True) if c.name != "scaffold_component"]
    panels_html: list[str] = []
    statuses: dict[str, str] = {}
    for comp in components:
        payload = _run_stats(comp)
        statuses[comp.name] = payload.get("status", "unknown")
        panels_html.append(_render_panel(comp, payload))

    template = TEMPLATE_PATH.read_text(encoding="utf-8") if TEMPLATE_PATH.is_file() else DEFAULT_TEMPLATE
    html_out = template.replace("{built_at}", datetime.now().strftime("%Y-%m-%d %H:%M"))
    html_out = html_out.replace("{panels}", "\n".join(panels_html))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_out, encoding="utf-8")
    return {"output": str(output_path), "components": list(statuses.keys()), "statuses": statuses}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=str(REPO_ROOT / "glance" / "dashboard" / "index.html"))
    p.add_argument("--no-migrate", action="store_true")
    args = p.parse_args(argv)
    result = build(Path(args.out), run_migrations=not args.no_migrate)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
