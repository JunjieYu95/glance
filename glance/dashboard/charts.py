"""Pure CSS/SVG chart renderers. Zero JavaScript dependencies.

Each function returns an HTML string to be embedded in a dashboard panel.
"""

from __future__ import annotations

import html as html_mod
import math
from typing import Any


def _esc(s: Any) -> str:
    return html_mod.escape(str(s))


def _no_data() -> str:
    return '<div class="chart-empty muted-row">No data</div>'


# ---------------------------------------------------------------------------
# Progress bar — horizontal CSS bar with label and value
# ---------------------------------------------------------------------------

def render_progress_bar(current: float, max_value: float, label: str = "",
                        unit: str = "", color: str = "var(--ok)") -> str:
    pct = min(current / max_value * 100, 100) if max_value > 0 else 0.0
    val_text = f"{current:.0f}{unit}/{max_value:.0f}{unit}" if unit else f"{current:.0f}/{max_value:.0f}"
    return f"""<div class="chart-progress">
  <span class="progress-label">{_esc(label)}</span>
  <div class="progress-track">
    <div class="progress-fill" style="width:{pct:.0f}%;background:{color}"></div>
  </div>
  <span class="progress-value">{_esc(val_text)}</span>
</div>"""


# ---------------------------------------------------------------------------
# Status card — rich card with icon, title, value, and status indicator
# ---------------------------------------------------------------------------

def render_status_card(title: str, value: str, status: bool | None = None,
                       status_label: str = "") -> str:
    if status is True:
        badge_class = "ok"
        badge_text = status_label or "done"
    elif status is False:
        badge_class = "bad"
        badge_text = status_label or "pending"
    else:
        badge_class = "muted"
        badge_text = status_label or "—"
    return f"""<div class="chart-status-card">
  <div class="status-title">{_esc(title)}</div>
  <div class="status-value">{_esc(value)}</div>
  <span class="badge {badge_class}">{_esc(badge_text)}</span>
</div>"""


# ---------------------------------------------------------------------------
# Bar chart — horizontal CSS bars
# ---------------------------------------------------------------------------

def render_bar_chart(data: list[dict], label_field: str = "label",
                     value_field: str = "value", max_value: float | None = None,
                     color: str = "var(--ok)") -> str:
    if not data:
        return _no_data()
    values = [d.get(value_field, 0) for d in data]
    max_v = max_value if max_value is not None else max(values)
    if max_v == 0:
        max_v = 1
    bars = []
    for d in data:
        v = d.get(value_field, 0)
        pct = (v / max_v * 100) if max_v > 0 else 0
        bars.append(f"""<div class="bar-item">
  <span class="bar-label">{_esc(d.get(label_field, ""))}</span>
  <div class="bar-track">
    <div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div>
  </div>
  <span class="bar-value">{_esc(v)}</span>
</div>""")
    return f'<div class="chart-bars">{"".join(bars)}</div>'


# ---------------------------------------------------------------------------
# Timeline — vertical CSS timeline with dots
# ---------------------------------------------------------------------------

def render_timeline(events: list[dict], time_field: str = "time",
                    title_field: str = "title",
                    desc_field: str = "") -> str:
    if not events:
        return _no_data()
    items = []
    for ev in events[:20]:  # limit to 20 items
        desc_html = ""
        if desc_field and ev.get(desc_field):
            desc_html = f'<div class="timeline-desc">{_esc(ev[desc_field])}</div>'
        items.append(f"""<div class="timeline-item">
  <div class="timeline-dot"></div>
  <div class="timeline-time">{_esc(ev.get(time_field, ""))}</div>
  <div class="timeline-content">
    <div class="timeline-title">{_esc(ev.get(title_field, ""))}</div>
    {desc_html}
  </div>
</div>""")
    return f'<div class="chart-timeline">{"".join(items)}</div>'


# ---------------------------------------------------------------------------
# Sparkline — inline SVG polyline
# ---------------------------------------------------------------------------

def render_sparkline(values: list[float], width: int = 200, height: int = 40,
                     color: str = "var(--ok)", line_width: int = 2) -> str:
    if not values:
        return ""
    if len(values) == 1:
        # Single value — draw a dot
        return (
            f'<svg width="{width}" height="{height}" class="chart-sparkline">'
            f'<circle cx="50%" cy="50%" r="3" fill="{color}"/>'
            f'</svg>'
        )
    min_v = min(values)
    max_v = max(values)
    v_range = max_v - min_v or 1  # avoid div-by-zero
    pad_x = 2
    pad_y = 2
    draw_w = width - pad_x * 2
    draw_h = height - pad_y * 2
    points = []
    for i, v in enumerate(values):
        x = pad_x + i * draw_w / (len(values) - 1)
        y = pad_y + draw_h - (v - min_v) * draw_h / v_range
        points.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg width="{width}" height="{height}" class="chart-sparkline">'
        f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" '
        f'stroke-width="{line_width}" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )


# ---------------------------------------------------------------------------
# Pie / Donut — SVG circle with conic-gradient segments via stroke-dasharray
# ---------------------------------------------------------------------------

_COLORS = [
    "#4a7", "#5b9", "#6cb", "#7dc", "#8ed", "#e8a", "#d79", "#c68",
    "#9ad", "#8bc", "#7ab", "#69a", "#a7d", "#b8e", "#c9f",
]


def render_pie_donut(data: list[dict], label_field: str = "label",
                     value_field: str = "value", donut: bool = False) -> str:
    if not data:
        return _no_data()
    total = sum(d.get(value_field, 0) for d in data)
    if total <= 0:
        return _no_data()

    # Limit to 15 slices to avoid visual clutter
    data = data[:15]

    size = 200
    center = size / 2
    r = 70
    inner_r = 35 if donut else 0
    stroke_width = r - inner_r
    # The effective circle drawn by the stroke is at radius (inner_r + stroke_width/2)
    eff_r = inner_r + stroke_width / 2
    circumference = 2 * math.pi * eff_r

    slices = []
    legend = []
    cumulative = 0.0

    for i, d in enumerate(data):
        pct = d.get(value_field, 0) / total
        if pct <= 0:
            continue
        seg_len = pct * circumference
        color = _COLORS[i % len(_COLORS)]
        label = _esc(d.get(label_field, ""))
        # Rotational offset: start from top (-90deg)
        # Convert cumulative fraction to dashoffset
        offset = circumference - cumulative * circumference
        slices.append(
            f'<circle cx="{center}" cy="{center}" r="{eff_r:.1f}" '
            f'fill="none" stroke="{color}" stroke-width="{stroke_width}" '
            f'stroke-dasharray="{seg_len:.1f} {circumference - seg_len:.1f}" '
            f'stroke-dashoffset="-{offset:.1f}" '
            f'transform="rotate(-90 {center} {center})"/>'
        )
        # Use <title> for tooltip on hover
        slices.append(
            f'<circle cx="{center}" cy="{center}" r="{eff_r:.1f}" '
            f'fill="none" stroke="transparent" stroke-width="{stroke_width}" '
            f'stroke-dasharray="{seg_len:.1f} {circumference - seg_len:.1f}" '
            f'stroke-dashoffset="-{offset:.1f}" '
            f'transform="rotate(-90 {center} {center})" class="pie-slice-hit">'
            f'<title>{label}: {_esc(d.get(value_field, ""))} ({pct*100:.0f}%)</title>'
            f'</circle>'
        )
        legend.append(
            f'<li><span class="legend-swatch" style="background:{color}"></span>'
            f'{label} ({pct*100:.0f}%)</li>'
        )
        cumulative += pct

    # Center hole for donut
    center_hole = ""
    if donut and inner_r > 0:
        center_hole = (
            f'<circle cx="{center}" cy="{center}" r="{inner_r}" '
            f'fill="var(--card, #fff)"/>'
            f'<text x="{center}" y="{center}" text-anchor="middle" '
            f'dominant-baseline="central" class="donut-center-text">'
            f'{total:.0f}</text>'
        )

    cls = "chart-donut" if donut else "chart-pie"
    return (
        f'<div class="{cls}-wrapper">'
        f'<svg viewBox="0 0 {size} {size}" class="{cls}" '
        f'width="{size}" height="{size}">'
        f'{"".join(slices)}'
        f'{center_hole}'
        f'</svg>'
        f'<ul class="chart-legend">{"".join(legend)}</ul>'
        f'</div>'
    )
