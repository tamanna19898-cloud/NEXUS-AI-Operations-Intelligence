"""
NEXUS AI - Data Loader Module
Handles secure, defensive ingestion of CSV and Excel files into pandas DataFrames.
"""

from io import BytesIO
import os
from pathlib import Path
from typing import Any, Union
import pandas as pd


class DataLoaderError(Exception):
    """Custom exception raised when dataset ingestion or validation fails."""
    pass


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def load_dataset(file_source: Union[str, Path, BytesIO, Any], file_name: str = "") -> pd.DataFrame:
    """
    Load a CSV or Excel file into a pandas DataFrame.
    
    Args:
        file_source: File path (str/Path), file-like buffer (BytesIO), or Streamlit UploadedFile.
        file_name: Optional explicit file name (used for format detection when file_source is a buffer).
        
    Returns:
        pd.DataFrame: A populated, cleaned pandas DataFrame.
        
    Raises:
        DataLoaderError: If the file is missing, empty, unsupported, or corrupted.
    """
    if file_source is None:
        raise DataLoaderError("No file provided. Please upload a valid CSV or Excel file.")

    # Determine file name and extension
    resolved_name = ""
    if isinstance(file_source, (str, Path)):
        resolved_name = str(file_source)
    elif hasattr(file_source, "name"):
        resolved_name = str(file_source.name)
    elif file_name:
        resolved_name = file_name
    else:
        resolved_name = "data.csv"

    ext = Path(resolved_name).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise DataLoaderError(
            f"Unsupported file format '{ext}'. Only CSV (.csv) and Excel (.xlsx, .xls) files are supported."
        )

    try:
        # Reset buffer pointer if applicable
        if hasattr(file_source, "seek"):
            file_source.seek(0)

        # Check empty buffer
        if hasattr(file_source, "getbuffer"):
            if file_source.getbuffer().nbytes == 0:
                raise DataLoaderError("The uploaded file is completely empty (0 bytes).")
        elif isinstance(file_source, (str, Path)):
            if not os.path.exists(file_source):
                raise DataLoaderError(f"File not found at path: {file_source}")
            if os.path.getsize(file_source) == 0:
                raise DataLoaderError("The file is empty (0 bytes).")

        # Parse CSV
        if ext == ".csv":
            try:
                # Try standard comma/autodetect engine
                df = pd.read_csv(file_source, sep=None, engine="python")
            except Exception:
                if hasattr(file_source, "seek"):
                    file_source.seek(0)
                try:
                    df = pd.read_csv(file_source)
                except Exception as csv_err:
                    raise DataLoaderError(f"Failed to parse CSV file: {str(csv_err)}")

        # Parse Excel
        elif ext in {".xlsx", ".xls"}:
            try:
                df = pd.read_excel(file_source)
            except Exception as excel_err:
                raise DataLoaderError(
                    f"Failed to parse Excel file. Ensure openpyxl is installed and file is valid: {str(excel_err)}"
                )

        if df is None or df.empty:
            raise DataLoaderError("The dataset contains no data rows.")

        if len(df.columns) == 0:
            raise DataLoaderError("The dataset contains no columns.")

        # Clean column names (strip whitespace)
        df.columns = [str(c).strip() for c in df.columns]

        return df

    except DataLoaderError:
        raise
    except Exception as exc:
        raise DataLoaderError(f"Unexpected error loading dataset: {str(exc)}")


def get_sample_datasets() -> dict[str, str]:
    """Returns available built-in demonstration datasets."""
    base_dir = Path(__file__).resolve().parent.parent / "sample_datasets"
    samples = {
        "Student Academic Performance": str(base_dir / "student_performance.csv"),
        "IPL Cricket Championship & Batsmen": str(base_dir / "ipl_cricket_stats.csv"),
        "Employee Salaries & HR": str(base_dir / "employee_salaries.csv"),
        "Retail Sales & Orders": str(base_dir / "retail_sales.csv"),
        "Hospitality Bookings": str(base_dir / "hospitality_bookings.csv"),
    }
    return {k: v for k, v in samples.items() if os.path.exists(v)}
