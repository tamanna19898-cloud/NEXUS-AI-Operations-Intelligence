"""
NEXUS AI - Data Analyzer Module
Calculates statistical summaries, column profiling, data completeness,
duplicate row detection, and automatic domain recognition.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def get_dataset_overview(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes top-level metadata and completeness KPIs for the dataset.
    
    Returns:
        dict: total_rows, total_cols, missing_values, missing_pct,
              duplicate_rows, duplicate_pct, memory_mb.
    """
    if df is None or df.empty:
        return {
            "total_rows": 0,
            "total_columns": 0,
            "missing_values": 0,
            "missing_pct": 0.0,
            "duplicate_rows": 0,
            "duplicate_pct": 0.0,
            "memory_mb": 0.0,
        }

    total_rows = len(df)
    total_cols = len(df.columns)
    total_cells = total_rows * total_cols
    missing_vals = int(df.isnull().sum().sum())
    missing_pct = round((missing_vals / total_cells * 100), 2) if total_cells > 0 else 0.0

    duplicate_rows = int(df.duplicated().sum())
    duplicate_pct = round((duplicate_rows / total_rows * 100), 2) if total_rows > 0 else 0.0

    memory_bytes = df.memory_usage(deep=True).sum()
    memory_mb = round(memory_bytes / (1024 * 1024), 2)

    return {
        "total_rows": total_rows,
        "total_columns": total_cols,
        "missing_values": missing_vals,
        "missing_pct": missing_pct,
        "duplicate_rows": duplicate_rows,
        "duplicate_pct": duplicate_pct,
        "memory_mb": memory_mb,
    }


def detect_column_types(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Classifies dataframe columns into numerical, categorical, and datetime groups.
    
    Returns:
        dict with keys 'numerical', 'categorical', 'datetime'.
    """
    numerical_cols: List[str] = []
    categorical_cols: List[str] = []
    datetime_cols: List[str] = []

    for col in df.columns:
        series = df[col]
        # Datetime check
        if pd.api.types.is_datetime64_any_dtype(series):
            datetime_cols.append(col)
        elif pd.api.types.is_numeric_dtype(series):
            # If numeric has only 2 unique values and name looks like flag, or object id
            numerical_cols.append(col)
        else:
            # Check if string could be datetime
            if series.dropna().shape[0] > 0:
                sample = str(series.dropna().iloc[0])
                # Quick regex/pattern check for dates like YYYY-MM-DD
                if len(sample) in (10, 19, 24) and ("-" in sample or "/" in sample):
                    try:
                        pd.to_datetime(series.dropna().head(20))
                        datetime_cols.append(col)
                        continue
                    except (ValueError, TypeError):
                        pass
            categorical_cols.append(col)

    return {
        "numerical": numerical_cols,
        "categorical": categorical_cols,
        "datetime": datetime_cols,
    }


def get_column_profiles(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generates structured profile information for each column in the DataFrame.
    """
    profiles = []
    total_rows = len(df)

    for col in df.columns:
        series = df[col]
        null_count = int(series.isnull().sum())
        null_pct = round((null_count / total_rows * 100), 1) if total_rows > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))

        if pd.api.types.is_numeric_dtype(series):
            col_type = "Numeric"
        elif pd.api.types.is_datetime64_any_dtype(series):
            col_type = "DateTime"
        elif pd.api.types.is_bool_dtype(series):
            col_type = "Boolean"
        else:
            col_type = "Categorical"

        # Safe sample values as preview
        sample_vals = [str(x) for x in series.dropna().unique()[:3]]
        sample_str = ", ".join(sample_vals) if sample_vals else "—"

        profiles.append({
            "column_name": col,
            "data_type": str(series.dtype),
            "category": col_type,
            "missing_count": null_count,
            "missing_pct": null_pct,
            "unique_values": unique_count,
            "sample_values": sample_str,
        })

    return profiles


def get_descriptive_stats(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Returns separate descriptive statistics DataFrames for numerical and categorical columns.
    """
    stats_dict: Dict[str, pd.DataFrame] = {}

    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        desc_num = numeric_df.describe().T.reset_index()
        desc_num.rename(columns={"index": "Column"}, inplace=True)
        # Round float columns cleanly
        for c in desc_num.columns:
            if c != "Column":
                desc_num[c] = desc_num[c].apply(lambda x: round(x, 2) if isinstance(x, (float, np.floating)) else x)
        stats_dict["numerical"] = desc_num

    cat_df = df.select_dtypes(include=["object", "category", "bool"])
    if not cat_df.empty:
        desc_cat = cat_df.describe().T.reset_index()
        desc_cat.rename(columns={"index": "Column"}, inplace=True)
        stats_dict["categorical"] = desc_cat

    return stats_dict


def get_missing_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a dataframe listing missing value counts and percentages sorted descending.
    """
    total_rows = len(df)
    missing_series = df.isnull().sum()
    pct_series = (missing_series / total_rows * 100).round(2) if total_rows > 0 else 0.0

    missing_df = pd.DataFrame({
        "Column": df.columns,
        "Missing Count": missing_series.values,
        "Missing (%)": pct_series.values,
        "Data Type": [str(df[col].dtype) for col in df.columns],
    })
    return missing_df.sort_values(by="Missing Count", ascending=False).reset_index(drop=True)


def get_correlation_matrix(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Returns Pearson correlation matrix if at least 2 numerical columns exist.
    """
    num_df = df.select_dtypes(include=[np.number])
    if num_df.shape[1] < 2:
        return None
    # Drop columns with 0 variance
    valid_cols = [c for c in num_df.columns if num_df[c].nunique(dropna=True) > 1]
    if len(valid_cols) < 2:
        return None
    corr = num_df[valid_cols].corr().round(3)
    return corr


def detect_dataset_domain(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Identifies the business or academic domain of the dataset using column signatures.
    """
    cols_lower = [c.lower() for c in df.columns]

    domains = {
        "Student & Academic Performance": {
            "keywords": ["student", "grade", "score", "exam", "reading", "math", "writing", "attendance", "study"],
            "description": "Educational records tracking student achievement, study habits, and test scores.",
        },
        "Human Resources & Payroll": {
            "keywords": ["employee", "salary", "department", "experience", "hire", "job", "performance", "attrition"],
            "description": "Organizational workforce data monitoring employee compensation and tenure.",
        },
        "Sales & E-Commerce": {
            "keywords": ["sales", "revenue", "order", "price", "quantity", "discount", "product", "profit"],
            "description": "Transactional commerce data measuring order volume, pricing, and revenue.",
        },
        "Hospitality & Reservations": {
            "keywords": ["hotel", "booking", "room", "guest", "adr", "nights", "lead_time", "checkin"],
            "description": "Hotel and lodging operations tracking room reservations, stay duration, and ADR.",
        },
        "Customer & Churn Analytics": {
            "keywords": ["customer", "churn", "tenure", "balance", "subscription", "spending", "segment"],
            "description": "Customer behavioral metrics analyzing engagement, lifetime value, and retention.",
        },
    }

    best_domain = "General Dataset"
    best_desc = "Multipurpose structured tabular dataset."
    max_matches = 0

    for domain_name, meta in domains.items():
        matches = sum(1 for kw in meta["keywords"] if any(kw in col for col in cols_lower))
        if matches > max_matches:
            max_matches = matches
            best_domain = domain_name
            best_desc = meta["description"]

    return {
        "domain": best_domain if max_matches >= 2 else "General Dataset",
        "description": best_desc if max_matches >= 2 else "Multipurpose structured tabular dataset.",
        "matched_signals": max_matches,
    }
