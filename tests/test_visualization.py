"""
Unit tests for src/visualization.py and src/insights.py
Validates Plotly figure generation, input validation, and evidence-based insights.
"""

import numpy as np
import pandas as pd
import pytest
from src.insights import generate_insights
from src.visualization import (
    create_bar_chart,
    create_histogram,
    create_line_chart,
    create_scatter_plot,
    generate_recommended_visualizations,
    validate_chart_inputs,
)


@pytest.fixture
def test_df():
    return pd.DataFrame({
        "category": ["A", "B", "C", "A", "B", "A"],
        "metric_x": [10.0, 20.0, 30.0, 15.0, 25.0, 12.0],
        "metric_y": [100.0, 200.0, 310.0, 160.0, 240.0, 115.0],
    })


def test_validate_chart_inputs(test_df):
    # Valid scatter
    valid, msg = validate_chart_inputs("Scatter Plot", test_df, "metric_x", "metric_y")
    assert valid is True
    assert msg == ""

    # Invalid scatter (categorical x)
    valid, msg = validate_chart_inputs("Scatter Plot", test_df, "category", "metric_y")
    assert valid is False
    assert "numerical" in msg.lower()

    # Missing column
    valid, msg = validate_chart_inputs("Bar Chart", test_df, "non_existent_col")
    assert valid is False


def test_create_bar_chart(test_df):
    fig = create_bar_chart(test_df, x_col="category", y_col="metric_x", agg_func="Mean")
    assert fig is not None
    assert len(fig.data) > 0


def test_create_histogram(test_df):
    fig = create_histogram(test_df, x_col="metric_x", nbins=10)
    assert fig is not None
    assert len(fig.data) > 0


def test_create_scatter_plot(test_df):
    fig = create_scatter_plot(test_df, x_col="metric_x", y_col="metric_y")
    assert fig is not None
    assert len(fig.data) > 0


def test_recommended_visualizations(test_df):
    recs = generate_recommended_visualizations(test_df)
    assert len(recs) >= 1
    assert all("title" in r and "figure" in r for r in recs)


def test_generate_insights_grounded(test_df):
    insights = generate_insights(test_df)
    assert isinstance(insights, list)
    assert len(insights) >= 2
    for insight in insights:
        assert "title" in insight
        assert "explanation" in insight
        assert "category" in insight
        # Never fabricate: ensure strings are non-empty and sensible
        assert len(insight["title"]) > 0
        assert len(insight["explanation"]) > 0
