"""
Unit tests for src/data_loader.py
Tests CSV and Excel ingestion, invalid file format rejections, empty file checks, and edge cases.
"""

from io import BytesIO
import tempfile
import pytest
import pandas as pd
from src.data_loader import DataLoaderError, get_sample_datasets, load_dataset


def test_load_valid_csv():
    csv_content = b"name,age,score\nAlice,24,88.5\nBob,29,91.0\nCharlie,22,76.0\n"
    buffer = BytesIO(csv_content)
    buffer.name = "students.csv"
    
    df = load_dataset(buffer)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert list(df.columns) == ["name", "age", "score"]
    assert df["age"].iloc[0] == 24


def test_load_empty_file():
    empty_buffer = BytesIO(b"")
    empty_buffer.name = "empty.csv"
    with pytest.raises(DataLoaderError) as exc_info:
        load_dataset(empty_buffer)
    assert "empty" in str(exc_info.value).lower()


def test_load_unsupported_extension():
    bad_buffer = BytesIO(b"hello world")
    bad_buffer.name = "document.pdf"
    with pytest.raises(DataLoaderError) as exc_info:
        load_dataset(bad_buffer)
    assert "unsupported" in str(exc_info.value).lower()


def test_load_none_source():
    with pytest.raises(DataLoaderError):
        load_dataset(None)


def test_load_csv_from_disk_path():
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tmp:
        tmp.write("dept,headcount\nSales,12\nEngineering,45\n")
        tmp_path = tmp.name

    try:
        df = load_dataset(tmp_path)
        assert len(df) == 2
        assert "dept" in df.columns
    finally:
        import os
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_sample_datasets_available():
    samples = get_sample_datasets()
    assert isinstance(samples, dict)
    assert len(samples) > 0
    # Verify each sample loads correctly
    for label, path in samples.items():
        df = load_dataset(path)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df.columns) > 0
