"""
Unit tests for src/data_analyzer.py
Validates metadata extraction, column type detection, descriptive statistics,
missing breakdown, correlation, and domain detection.
"""

import numpy as np
import pandas as pd
import pytest
from src.data_analyzer import (
    detect_column_types,
    detect_dataset_domain,
    get_column_profiles,
    get_correlation_matrix,
    get_dataset_overview,
    get_descriptive_stats,
    get_missing_breakdown,
)


@pytest.fixture
def sample_mixed_df():
    return pd.DataFrame({
        "student_id": ["S1", "S2", "S3", "S4", "S4"],  # Contains duplicate row test
        "grade_level": ["10th", "11th", "10th", "12th", "12th"],
        "math_score": [85.0, 92.0, np.nan, 78.0, 78.0],
        "reading_score": [88.0, 90.0, 75.0, 82.0, 82.0],
    })


def test_dataset_overview(sample_mixed_df):
    overview = get_dataset_overview(sample_mixed_df)
    assert overview["total_rows"] == 5
    assert overview["total_columns"] == 4
    assert overview["missing_values"] == 1  # 1 NaN in math_score
    assert overview["duplicate_rows"] == 1  # row 3 and 4 are identical


def test_detect_column_types(sample_mixed_df):
    types = detect_column_types(sample_mixed_df)
    assert "math_score" in types["numerical"]
    assert "reading_score" in types["numerical"]
    assert "student_id" in types["categorical"]
    assert "grade_level" in types["categorical"]


def test_column_profiles(sample_mixed_df):
    profiles = get_column_profiles(sample_mixed_df)
    assert len(profiles) == 4
    math_prof = next(p for p in profiles if p["column_name"] == "math_score")
    assert math_prof["missing_count"] == 1
    assert math_prof["category"] == "Numeric"


def test_descriptive_stats(sample_mixed_df):
    stats = get_descriptive_stats(sample_mixed_df)
    assert "numerical" in stats
    assert "categorical" in stats
    num_df = stats["numerical"]
    assert "math_score" in num_df["Column"].values
    assert "mean" in num_df.columns


def test_missing_breakdown(sample_mixed_df):
    missing_df = get_missing_breakdown(sample_mixed_df)
    assert len(missing_df) == 4
    # The first row should be the one with missing values
    assert missing_df.iloc[0]["Column"] == "math_score"
    assert missing_df.iloc[0]["Missing Count"] == 1


def test_correlation_matrix(sample_mixed_df):
    corr = get_correlation_matrix(sample_mixed_df)
    assert corr is not None
    assert "math_score" in corr.columns
    assert "reading_score" in corr.columns
    assert corr.loc["reading_score", "reading_score"] == 1.0


def test_detect_student_domain(sample_mixed_df):
    domain_info = detect_dataset_domain(sample_mixed_df)
    assert "Student" in domain_info["domain"]


def test_empty_dataframe_handling():
    empty_df = pd.DataFrame()
    overview = get_dataset_overview(empty_df)
    assert overview["total_rows"] == 0
    assert overview["missing_values"] == 0
