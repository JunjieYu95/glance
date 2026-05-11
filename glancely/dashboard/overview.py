"""Overview panel — replicates the reference dashboard's "Last 14 Days" grid.

Style: mood→sized dot, progress→mini bar, MIT-style→colored dot (green/rose/absent),
badge→checkmark text, number row under bars.
"""

from __future__ import annotations

import html as html_mod
from datetime import date, datetime, timedelta
from typing import Any, Callable


def _esc(s: Any) -> str:
    return html_mod.escape(str(s))


def _parse_date(val: Any) -> date | None:
    if not val:
        return None
    if isinstance(val, date):
        return val
    s = str(val)[:10]
    try:
        return datetime.fromisoformat(s).date()
    except (ValueError, TypeError):
        return None


def _fmt_hours(minutes: float) -> str:
    if minutes < 60:
        return f"{minutes:.0f}m"
    return f"{minutes / 60:.1f}h"


def _collect_daily_metrics(
    components_meta: list[dict], num_days: int = 14
) -> tuple[list[date], list[dict], list[int | None]]:
    today = date.today()
    days = [(today - timedelta(days=d)) for d in range(num_days - 1, -1, -1)]
    metrics: list[dict] = []
    max_prod: list[int | None] = [None]  # mutable to share with prod text row

    for meta in components_meta:
        ov = meta.get("overview", {})
        if ov.get("enabled") is False:
            continue
        payload = meta.get("payload", {})
        rows = payload.get("rows", [])
        card_type = ov.get("card_type", "stat")
        label = ov.get("label", meta.get("title", meta.get("name", "")))
        color = ov.get("color", "")

        if not rows:
            continue

        if card_type == "badge":
            daily = {d: False for d in days}
            for r in rows:
                dt = _parse_date(r.get(ov.get("date_field", "created_at")))
                if dt and dt in set(days):
                    daily[dt] = True
            metrics.append({
                "label": label, "style": "mit", "color": color or "#22c55e",
                "values": daily,
            })

        elif card_type == "progress":
            value_field = ov.get("value_field", "value")
            date_field = ov.get("date_field", "created_at")
            daily: dict[date, float] = {d: 0 for d in days}
            for r in rows:
                dt = _parse_date(r.get(date_field))
                if dt and dt in set(days):
                    try:
                        daily[dt] += float(r.get(value_field, 0))
                    except (ValueError, TypeError):
                        pass
            vals = [v for v in daily.values() if v > 0]
            max_v = max(vals) if vals else 1
            metrics.append({
                "label": label, "style": "bar", "color": color or "#2dd4bf",
                "values": daily, "max_value": max_v,
            })
            # Add a number row right after the bar row
            if card_type == "progress":
                metrics.append({
                    "label": "", "style": "number",
                    "values": daily, "max_value": max_v,
                })

        elif card_type == "sparkline":
            value_field = ov.get("value_field", "value")
            daily: dict[date, float | None] = {d: None for d in days}
            for r in rows:
                dt = _parse_date(r.get("created_at"))
                if dt and dt in set(days):
                    try:
                        daily[dt] = float(r.get(value_field, 0))
                    except (ValueError, TypeError):
                        pass
            vals = [v for v in daily.values() if v is not None]
            max_v = max(vals) if vals else 1
            metrics.append({
                "label": label, "style": "mood", "color": color or "#22c55e",
                "values": daily, "max_value": max_v,
            })

        else:  # stat — count per day
            daily: dict[date, int] = {d: 0 for d in days}
            for r in rows:
                dt = _parse_date(r.get("created_at"))
                if dt and dt in set(days):
                    daily[dt] += 1
            vals = [v for v in daily.values() if v > 0]
            max_v = max(vals) if vals else 1
            metrics.append({
                "label": label, "style": "mood", "color": color or "#38bdf8",
                "values": daily, "max_value": max_v,
            })

    return days, metrics, max_prod


def render_overview_panel(components_meta: list[dict], num_days: int = 14) -> str:
    days, metrics, _ = _collect_daily_metrics(components_meta, num_days)
    if not metrics:
        return ""

    # Day header row
    day_labels = "".join(
        f"<div class=\"ov-day-label\">{d.strftime('%-d')}<br>{d.strftime('%a')[:1]}</div>"
        for d in days
    )

    # Legend
    style_colors = {}
    for m in metrics:
        if m.get("label"):
            style_colors.setdefault(m["style"], m.get("color", "#38bdf8"))
    legend_parts = []
    for st, color in style_colors.items():
        if st == "bar":
            legend_parts.append(f'<span><i class="dot" style="background:{color}"></i>bar</span>')
        elif st == "mood":
            legend_parts.append(f'<span><i class="dot" style="background:{color}"></i>mood</span>')
        elif st == "mit":
            legend_parts.append(f'<span><i class="dot" style="background:{color}"></i>done</span>')
    legend = "".join(legend_parts) if legend_parts else ""

    rows_html = []
    for m in metrics:
        label = m["label"]
        row_label = f"<div class=\"ov-row-label\">{_esc(label)}</div>" if label else '<div class="ov-row-label"></div>'
        cells = _render_row(days, m)
        rows_html.append(f"{row_label}{cells}")

    rows_str = "".join(rows_html)
    return (
        '<section class="panel overview-panel">'
        '<div class="panel-head">'
        f"<h2>Last {len(days)} Days</h2>"
        f'<span class="legend">{legend}</span>'
        '</div>'
        '<div class="overview">'
        f'<div class="ov-row-label ov-header"></div>{day_labels}'
        f'{rows_str}'
        '</div>'
        '</section>'
    )


def _render_row(days: list[date], m: dict) -> str:
    style = m.get("style", "mood")
    renderers: dict[str, Callable] = {
        "mood": _render_mood_style,
        "bar": _render_bar_style,
        "mit": _render_mit_style,
        "number": _render_number_style,
    }
    renderer = renderers.get(style, _render_mood_style)
    return renderer(days, m)


def _render_mood_style(days: list[date], m: dict) -> str:
    """Colored dot — size proportional to value count."""
    values = m["values"]
    max_v = m.get("max_value", 1) or 1
    color = m.get("color", "#22c55e")
    cells = []
    for d in days:
        v = values.get(d)
        if v is None or v == 0:
            cells.append('<div class="mood-cell"></div>')
        else:
            size = min(20, 8 + int(float(v) / max_v * 12))
            cells.append(
                f'<div class="mood-cell" title="{_esc(d)}: {v:.0f}">'
                f'<div class="mood-dot" style="width:{size}px;height:{size}px;'
                f'background:{color}"></div></div>'
            )
    return "".join(cells)


def _render_bar_style(days: list[date], m: dict) -> str:
    """Mini bar — like prod hours."""
    values = m["values"]
    max_v = m.get("max_value", 1) or 1
    color = m.get("color", "#2dd4bf")
    cells = []
    for d in days:
        v = values.get(d, 0)
        if v == 0:
            cells.append('<div class="prod-cell"></div>')
        else:
            pct = min(float(v) / max_v * 100, 100) if max_v > 0 else 0
            cells.append(
                f'<div class="prod-cell" title="{_esc(d)}: {_fmt_hours(v)}">'
                f'<div class="prod-bar" style="height:{pct:.0f}%;'
                f'background:{color}"></div></div>'
            )
    return "".join(cells)


def _render_number_style(days: list[date], m: dict) -> str:
    """Small number text under bar cells."""
    values = m["values"]
    cells = []
    for d in days:
        v = values.get(d, 0)
        text = _fmt_hours(v) if v >= 30 else ""
        cells.append(f'<div class="prod-num">{_esc(text)}</div>')
    return "".join(cells)


def _render_mit_style(days: list[date], m: dict) -> str:
    """Green/rose dot — like MIT status or GP/NP."""
    values = m["values"]
    color = m.get("color", "#22c55e")
    cells = []
    for d in days:
        v = values.get(d, False)
        if v:
            cells.append(
                f'<div class="mit-cell" title="{_esc(d)}: done">'
                f'<div class="mit-dot done" style="background:{color}"></div></div>'
            )
        else:
            cells.append(
                '<div class="mit-cell" title="absent">'
                '<div class="mit-dot absent"></div></div>'
            )
    return "".join(cells)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    if not hex_color or not hex_color.startswith("#"):
        return (56, 189, 248)
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def resolve_data_key(payload: dict, data_key: str) -> Any:
    parts = data_key.split(".")
    current: Any = payload
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current
