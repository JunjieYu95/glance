"""Overview panel — calendar-grid summary using text markers per cell.

Renders a "Last N Days" table where each row is a tracker, each column is a day,
and each cell shows a short text marker (number, word, or symbol) with
color-coded background intensity.
"""

from __future__ import annotations

import html as html_mod
from datetime import date, datetime, timedelta
from typing import Any


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


def _collect_daily_metrics(
    components_meta: list[dict], num_days: int = 14
) -> tuple[list[date], list[dict]]:
    today = date.today()
    days = [(today - timedelta(days=d)) for d in range(num_days - 1, -1, -1)]
    metrics: list[dict] = []

    for meta in components_meta:
        ov = meta.get("overview", {})
        if ov.get("enabled") is False:
            continue
        payload = meta.get("payload", {})
        rows = payload.get("rows", [])
        card_type = ov.get("card_type", "stat")
        key = meta.get("name", "")
        label = ov.get("label", meta.get("title", key))
        color = ov.get("color", "")

        if not rows:
            continue

        if card_type == "badge":
            # Boolean: show checkmark or empty
            daily = {d: False for d in days}
            for r in rows:
                dt = _parse_date(r.get(ov.get("date_field", "created_at")))
                if dt and dt in set(days):
                    daily[dt] = True
            metrics.append({
                "key": key, "label": label, "type": "marker",
                "color": color or "#22c55e",
                "true_marker": "✓",
                "values": daily,
            })

        elif card_type == "sparkline":
            # Numeric: show number
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
                "key": key, "label": label, "type": "number",
                "color": color or "#38bdf8",
                "values": daily,
                "max_value": max_v,
            })

        elif card_type == "progress":
            # Sum per day, show number
            value_field = ov.get("value_field", "value")
            daily: dict[date, int] = {d: 0 for d in days}
            for r in rows:
                dt = _parse_date(r.get(ov.get("date_field", "created_at")))
                if dt and dt in set(days):
                    try:
                        daily[dt] += int(float(r.get(value_field, 0)))
                    except (ValueError, TypeError):
                        pass
            vals = [v for v in daily.values() if v > 0]
            max_v = max(vals) if vals else 1
            metrics.append({
                "key": key, "label": label, "type": "number",
                "color": color or "#a78bfa",
                "values": daily,
                "max_value": max_v,
            })

        else:  # stat — per-day count
            daily: dict[date, int] = {d: 0 for d in days}
            for r in rows:
                dt = _parse_date(r.get("created_at"))
                if dt and dt in set(days):
                    daily[dt] += 1
            vals = [v for v in daily.values() if v > 0]
            max_v = max(vals) if vals else 1
            metrics.append({
                "key": key, "label": label, "type": "number",
                "color": color or "#8aa2b8",
                "values": daily,
                "max_value": max_v,
            })

    return days, metrics


def render_overview_panel(components_meta: list[dict], num_days: int = 14) -> str:
    """Render a calendar-grid overview using text marker cells."""
    days, metrics = _collect_daily_metrics(components_meta, num_days)

    if not metrics:
        return ""

    day_labels = "".join(
        f"<div class=\"ov-day-label\">{d.strftime('%-d')}<br>{d.strftime('%a')[:1]}</div>"
        for d in days
    )

    rows_html = []
    for m in metrics:
        row_label = f"<div class=\"ov-row-label\">{_esc(m['label'])}</div>"
        cells = _render_marker_cells(days, m)
        rows_html.append(f"{row_label}{cells}")

    rows_str = "".join(rows_html)
    return (
        '<section class="panel overview-panel">'
        f"<header><h2>Last {num_days} Days</h2></header>"
        '<div class="overview-grid-cal">'
        f"<div class=\"ov-row-label ov-header\"></div>{day_labels}"
        f"{rows_str}"
        "</div>"
        "</section>"
    )


def _render_marker_cells(days: list[date], m: dict) -> str:
    """Render text marker cells with color-coded background intensity."""
    cells_html = []
    typ = m.get("type", "number")
    values = m["values"]
    max_v = m.get("max_value", 1) or 1
    color = m.get("color", "#38bdf8")
    r, g, b = _hex_to_rgb(color)

    for d in days:
        v = values.get(d)
        if v is None or v == 0 or v is False:
            cells_html.append('<div class="ov-cell ov-empty"></div>')
            continue

        if typ == "marker":
            marker = m.get("true_marker", "✓")
            cells_html.append(
                f'<div class="ov-cell ov-marker" style="color:{color}" '
                f'title="{_esc(d)}">{marker}</div>'
            )
        else:
            # Number: show value, intensity = ratio to max
            intensity = min(float(v) / max_v, 1.0) if max_v > 0 else 0
            alpha = 0.1 + intensity * 0.6
            bg = f"rgba({r},{g},{b},{alpha:.2f})"
            txt = str(int(v)) if isinstance(v, (int, float)) and v == int(v) else f"{v:.0f}"
            cells_html.append(
                f'<div class="ov-cell ov-num" style="background:{bg};color:{color}" '
                f'title="{_esc(d)}: {v}">{txt}</div>'
            )

    return "".join(cells_html)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    if not hex_color or not hex_color.startswith("#"):
        return (56, 189, 248)  # default blue
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
