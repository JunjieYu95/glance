# tests/test_dashboard_charts.py
"""Unit tests for chart config loading, rendering, and dispatch."""

from __future__ import annotations

import html
import pytest
from pathlib import Path


# ============================================================================
# SVG chart renderer tests (Task 5)
# ============================================================================


def test_render_sparkline():
    from glance.dashboard.charts import render_sparkline
    html_out = render_sparkline([3, 7, 5, 9, 6, 8, 7], width=200, height=40)
    assert "<svg" in html_out
    assert "<polyline" in html_out
    assert 'points="' in html_out


def test_render_sparkline_single_value():
    from glance.dashboard.charts import render_sparkline
    html_out = render_sparkline([5], width=200, height=40)
    assert "<svg" in html_out


def test_render_sparkline_empty():
    from glance.dashboard.charts import render_sparkline
    html_out = render_sparkline([], width=200, height=40)
    assert html_out == ""


def test_render_pie_chart():
    from glance.dashboard.charts import render_pie_donut
    data = [{"label": "prod", "value": 240}, {"label": "admin", "value": 72}, {"label": "meetings", "value": 88}]
    html_out = render_pie_donut(data, label_field="label", value_field="value", donut=False)
    assert "<svg" in html_out
    assert "prod" in html_out
    assert 'class="chart-pie"' in html_out


def test_render_donut_chart():
    from glance.dashboard.charts import render_pie_donut
    data = [{"label": "prod", "value": 240}, {"label": "admin", "value": 72}]
    html_out = render_pie_donut(data, label_field="label", value_field="value", donut=True)
    assert "<svg" in html_out
    assert 'class="chart-donut"' in html_out


def test_render_pie_donut_empty():
    from glance.dashboard.charts import render_pie_donut
    html_out = render_pie_donut([], label_field="x", value_field="y")
    assert "No data" in html_out


def test_render_pie_donut_zero_total():
    from glance.dashboard.charts import render_pie_donut
    data = [{"label": "a", "value": 0}, {"label": "b", "value": 0}]
    html_out = render_pie_donut(data, label_field="label", value_field="value")
    assert "No data" in html_out


# ============================================================================
# Stateless chart renderer tests (Task 4)
# ============================================================================


def test_render_progress_bar():
    from glance.dashboard.charts import render_progress_bar
    html_out = render_progress_bar(current=7, max_value=10, label="Done")
    assert "width:70%" in html_out
    assert "Done" in html_out
    assert "7/10" in html_out


def test_render_progress_bar_zero_max():
    from glance.dashboard.charts import render_progress_bar
    html_out = render_progress_bar(current=0, max_value=0, label="N/A")
    assert "width:0%" in html_out


def test_render_status_card_ok():
    from glance.dashboard.charts import render_status_card
    html_out = render_status_card(
        title="Today's MIT",
        value="Design the API",
        status=True,
    )
    assert "Today" in html_out and "MIT" in html_out
    assert "Design the API" in html_out
    assert "ok" in html_out


def test_render_status_card_incomplete():
    from glance.dashboard.charts import render_status_card
    html_out = render_status_card(
        title="Today's MIT",
        value="Not set",
        status=False,
    )
    assert "Not set" in html_out
    assert "bad" in html_out or "muted" in html_out


def test_render_bar_chart():
    from glance.dashboard.charts import render_bar_chart
    data = [{"label": "prod", "value": 240}, {"label": "admin", "value": 72}]
    html_out = render_bar_chart(data, label_field="label", value_field="value")
    assert "prod" in html_out
    assert "240" in html_out


def test_render_bar_chart_empty():
    from glance.dashboard.charts import render_bar_chart
    html_out = render_bar_chart([], label_field="x", value_field="y")
    assert "No data" in html_out or "no data" in html_out


def test_render_timeline():
    from glance.dashboard.charts import render_timeline
    events = [
        {"time": "14:30", "title": "Wrapper refactor"},
        {"time": "15:45", "title": "Code review"},
    ]
    html_out = render_timeline(events, time_field="time", title_field="title")
    assert "Wrapper refactor" in html_out
    assert "timeline" in html_out  # CSS class


# ============================================================================
# Config loading tests (Task 2)
# ============================================================================


def test_load_chart_config_returns_none_for_missing_file(tmp_path):
    from glance.dashboard.load_chart_config import load_chart_config
    comp_dir = tmp_path / "no_config"
    comp_dir.mkdir()
    result = load_chart_config(comp_dir)
    assert result is None


def test_load_chart_config_parses_valid_heatmap(tmp_path):
    from glance.dashboard.load_chart_config import load_chart_config
    comp_dir = tmp_path / "valid_heatmap"
    comp_dir.mkdir()
    (comp_dir / "chart.toml").write_text("""\
[chart]
type = "heatmap"
title = "Mood Heatmap"

[chart.data]
source = "rows"
date_field = "created_at"
value_field = "mood_score"
label_field = "mood_label"

[chart.options]
color_scheme = "green"

[overview]
enabled = true
card_type = "sparkline"
label = "Mood"
data_key = "summary.avg_score_7d"
suffix = "/10"
""")
    result = load_chart_config(comp_dir)
    assert result is not None
    assert result["chart"]["type"] == "heatmap"
    assert result["chart"]["data"]["date_field"] == "created_at"
    assert result["overview"]["enabled"] is True
    assert result["overview"]["card_type"] == "sparkline"


def test_load_chart_config_rejects_invalid_type(tmp_path):
    from glance.dashboard.load_chart_config import load_chart_config
    comp_dir = tmp_path / "invalid"
    comp_dir.mkdir()
    (comp_dir / "chart.toml").write_text("""\
[chart]
type = "garbage"
[chart.data]
source = "rows"
""")
    with pytest.raises(ValueError, match="Unsupported chart type"):
        load_chart_config(comp_dir)


def test_load_chart_config_missing_data_section(tmp_path):
    from glance.dashboard.load_chart_config import load_chart_config
    comp_dir = tmp_path / "no_data"
    comp_dir.mkdir()
    (comp_dir / "chart.toml").write_text("""\
[chart]
type = "bar"
""")
    with pytest.raises(ValueError, match="chart.data"):
        load_chart_config(comp_dir)
