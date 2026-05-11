"""Overview panel — calendar-grid summary compositing all tracker data by day."""

from __future__ import annotations

import html as html_mod
from datetime import date, datetime, timedelta
from typing import Any


def _esc(s: Any) -> str:
    return html_mod.escape(str(s))


def _parse_date(val: Any) -> date | None:
    """Parse various date formats from tracker rows."""
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
    """Collect per-day metrics from all contributing components.

    Returns (days, metrics) where metrics is a list of dicts:
      {key: str, label: str, values: dict[date, Any]}
    """
    today = date.today()
    days = [(today - timedelta(days=d)) for d in range(num_days - 1, -1, -1)]
    metrics: list[dict] = []

    contributing = [
        m for m in components_meta
        if m.get("overview", {}).get("enabled") is not False
    ]

    for meta in contributing:
        ov = meta.get("overview", {})
        payload = meta.get("payload", {})
        rows = payload.get("rows", [])
        card_type = ov.get("card_type", "stat")
        key = meta.get("name", "")
        label = ov.get("label", meta.get("title", key))
        color = ov.get("color", "var(--blue)")

        if not rows:
            continue

        if card_type == "sparkline":
            # For heatmap-like trackers: collect daily values
            value_field = ov.get("value_field", "value")
            daily: dict[date, float | None] = {}
            for r in rows:
                dt = _parse_date(r.get("created_at"))
                if dt and dt in set(days):
                    try:
                        daily[dt] = float(r.get(value_field, 0))
                    except (ValueError, TypeError):
                        daily[dt] = None
            metrics.append({
                "key": key, "label": label, "type": "heat",
                "color": color or "var(--green)",
                "values": {d: daily.get(d) for d in days},
            })

        elif card_type == "badge":
            # Boolean/binary trackers: per-day presence
            date_field = ov.get("date_field", "created_at")
            daily_presence: dict[date, bool] = {d: False for d in days}
            for r in rows:
                dt = _parse_date(r.get(date_field))
                if dt and dt in set(days):
                    daily_presence[dt] = True
            metrics.append({
                "key": key, "label": label, "type": "dot",
                "color": color or "var(--amber)",
                "values": daily_presence,
            })

        elif card_type == "progress":
            # Numeric progress: sum per day
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
            max_v = max(daily.values()) if daily else 1
            metrics.append({
                "key": key, "label": label, "type": "bar",
                "color": color or "var(--blue)",
                "values": daily,
                "max_value": max_v,
            })

        else:  # "stat" — per-day count
            daily_count: dict[date, int] = {d: 0 for d in days}
            for r in rows:
                dt = _parse_date(r.get("created_at"))
                if dt and dt in set(days):
                    daily_count[dt] += 1
            metrics.append({
                "key": key, "label": label, "type": "count",
                "color": color or "var(--muted)",
                "values": daily_count,
            })

    return days, metrics


def render_overview_panel(components_meta: list[dict], num_days: int = 14) -> str:
    """Render a calendar-grid overview compositing daily signals from all trackers.

    Produces a table where rows = trackers, columns = days, cells show
    colored indicators based on metric type (heat, dot, bar, count).
    """
    days, metrics = _collect_daily_metrics(components_meta, num_days)

    if not metrics:
        return ""

    # Build CSS grid: row-label column + one column per day
    day_labels = "".join(
        f"<div class=\"ov-day-label\">{d.strftime('%-d')}<br>{d.strftime('%a')[:1]}</div>"
        for d in days
    )

    rows_html = []
    color_map = {
        "heat": _render_heat_cells,
        "dot": _render_dot_cells,
        "bar": _render_bar_cells,
        "count": _render_count_cells,
    }

    for m in metrics:
        row_label = f"<div class=\"ov-row-label\">{_esc(m['label'])}</div>"
        renderer = color_map.get(m["type"], _render_count_cells)
        cells = renderer(days, m)
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


def _render_heat_cells(days: list[date], m: dict) -> str:
    """Render heatmap cells: color intensity by value."""
    values = m["values"]
    vals = [v for v in values.values() if v is not None]
    max_v = max(vals) if vals else 1
    cells = []
    for d in days:
        v = values.get(d)
        if v is None:
            cells.append('<div class="ov-cell ov-empty"></div>')
        else:
            intensity = min(v / max_v, 1.0) if max_v > 0 else 0
            r, g, b = _hex_to_rgb(m.get("color", "#22c55e"))
            bg = f"rgba({r},{g},{b},{0.15 + intensity * 0.85:.2f})"
            cells.append(
                f'<div class="ov-cell ov-heat" style="background:{bg}" '
                f'title="{_esc(d)}: {v:.0f}"></div>'
            )
    return "".join(cells)


def _render_dot_cells(days: list[date], m: dict) -> str:
    """Render binary dot cells: filled dot if true."""
    values = m["values"]
    color = m.get("color", "var(--amber)")
    cells = []
    for d in days:
        if values.get(d):
            cells.append(
                f'<div class="ov-cell ov-dot" style="background:{color}" '
                f'title="{_esc(d)}"></div>'
            )
        else:
            cells.append('<div class="ov-cell ov-empty"></div>')
    return "".join(cells)


def _render_bar_cells(days: list[date], m: dict) -> str:
    """Render mini bar cells: height proportional to value."""
    values = m["values"]
    max_v = max(values.values()) if values and max(values.values()) > 0 else 1
    cells = []
    for d in days:
        v = values.get(d, 0)
        pct = min(v / max_v * 100, 100) if max_v > 0 else 0
        cells.append(
            f'<div class="ov-cell ov-bar" title="{_esc(d)}: {v:.0f}">'
            f'<div class="ov-bar-fill" style="height:{pct:.0f}%;'
            f'background:{m.get("color","var(--blue)")}"></div></div>'
        )
    return "".join(cells)


def _render_count_cells(days: list[date], m: dict) -> str:
    """Render count cells: number displayed."""
    values = m["values"]
    max_v = max(values.values()) if values and max(values.values()) > 0 else 1
    cells = []
    for d in days:
        v = values.get(d, 0)
        intensity = min(v / max_v, 1.0) if max_v > 0 else 0
        r, g, b = _hex_to_rgb("#38bdf8")
        bg = f"rgba({r},{g},{b},{0.1 + intensity * 0.5:.2f})" if v > 0 else "transparent"
        txt = str(v) if v > 0 else ""
        cells.append(
            f'<div class="ov-cell ov-count" style="background:{bg}" '
            f'title="{_esc(d)}: {v}">{txt}</div>'
        )
    return "".join(cells)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple. Falls back to blue for CSS variables."""
    if not hex_color.startswith("#"):
        return (56, 189, 248)  # default blue
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def resolve_data_key(payload: dict, data_key: str) -> Any:
    """Resolve a dot-notation path into a stats payload dict."""
    parts = data_key.split(".")
    current: Any = payload
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current
