"""Overview panel — calendar-grid with per-row visual styles.

Mimics the reference dashboard: mood→colored dot, progress→mini-bar+number,
badge→checkmark, stat→colored dot.
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
                "label": label, "style": "marker",
                "color": color or "#22c55e",
                "marker": "✓",
                "values": daily,
            })

        elif card_type == "sparkline":
            # Numeric with per-day values → use dot (mood-like)
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
                "label": label, "style": "dot",
                "color": color or "#22c55e",
                "values": daily,
                "max_value": max_v,
            })

        elif card_type in ("progress", "stat"):
            # Numeric → mini bar + number on top
            value_field = ov.get("value_field", "value")
            date_field = ov.get("date_field", "created_at")
            if card_type == "progress":
                daily: dict[date, int] = {d: 0 for d in days}
                for r in rows:
                    dt = _parse_date(r.get(date_field))
                    if dt and dt in set(days):
                        try:
                            daily[dt] += int(float(r.get(value_field, 0)))
                        except (ValueError, TypeError):
                            pass
            else:
                daily = {d: 0 for d in days}
                for r in rows:
                    dt = _parse_date(r.get(date_field if "date_field" in ov else "created_at"))
                    if dt and dt in set(days):
                        daily[dt] += 1
            vals = [v for v in daily.values() if v > 0]
            max_v = max(vals) if vals else 1
            metrics.append({
                "label": label, "style": "bar",
                "color": color or "#38bdf8",
                "values": daily,
                "max_value": max_v,
            })

    return days, metrics


def render_overview_panel(components_meta: list[dict], num_days: int = 14) -> str:
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
        cells = _render_row(days, m)
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


def _render_row(days: list[date], m: dict) -> str:
    style = m.get("style", "dot")
    renderers: dict[str, Callable] = {
        "dot": _render_dot,
        "bar": _render_bar,
        "marker": _render_marker,
    }
    renderer = renderers.get(style, _render_dot)
    return renderer(days, m)


def _render_dot(days: list[date], m: dict) -> str:
    """Colored dot (mood style): size varies by value."""
    values = m["values"]
    max_v = m.get("max_value", 1) or 1
    color = m.get("color", "#22c55e")
    cells = []
    for d in days:
        v = values.get(d)
        if v is None or v == 0:
            cells.append('<div class="ov-cell ov-empty"></div>')
        else:
            size = min(16, 6 + int(float(v) / max_v * 10))
            cells.append(
                f'<div class="ov-cell ov-dot-wrap" title="{_esc(d)}: {v:.0f}">'
                f'<div class="ov-dot" style="width:{size}px;height:{size}px;'
                f'background:{color}"></div></div>'
            )
    return "".join(cells)


def _render_bar(days: list[date], m: dict) -> str:
    """Mini bar with number on top (prod style)."""
    values = m["values"]
    max_v = m.get("max_value", 1) or 1
    color = m.get("color", "#38bdf8")
    cells = []
    for d in days:
        v = values.get(d, 0)
        if v == 0:
            cells.append('<div class="ov-cell ov-empty"></div>')
        else:
            pct = min(float(v) / max_v * 100, 100) if max_v > 0 else 0
            cells.append(
                f'<div class="ov-cell ov-bar-cell" title="{_esc(d)}: {v}">'
                f'<span class="ov-bar-num">{int(v)}</span>'
                f'<div class="ov-bar-track"><div class="ov-bar-fill" '
                f'style="height:{pct:.0f}%;background:{color}"></div></div>'
                f"</div>"
            )
    return "".join(cells)


def _render_marker(days: list[date], m: dict) -> str:
    """Checkmark or empty (GP/NP style)."""
    values = m["values"]
    color = m.get("color", "#22c55e")
    marker = m.get("marker", "✓")
    cells = []
    for d in days:
        if values.get(d):
            cells.append(
                f'<div class="ov-cell ov-marker" style="color:{color}" '
                f'title="{_esc(d)}">{marker}</div>'
            )
        else:
            cells.append('<div class="ov-cell ov-empty"></div>')
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
