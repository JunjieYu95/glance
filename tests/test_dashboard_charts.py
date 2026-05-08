# tests/test_dashboard_charts.py
"""Unit tests for chart config loading, rendering, and dispatch."""

from __future__ import annotations

import html
import pytest
from pathlib import Path


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
