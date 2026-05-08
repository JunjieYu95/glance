"""Pure CSS/SVG chart renderers. Zero JavaScript dependencies.

Each function returns an HTML string to be embedded in a dashboard panel.
"""

from __future__ import annotations

import html as html_mod
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
