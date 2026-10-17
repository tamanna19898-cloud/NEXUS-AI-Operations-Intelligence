"""
NEXUS AI - Insights Module
Generates strictly evidence-based, grounded statistical insights from tabular data.
Never fabricates results; computes exact statistics from pandas DataFrames.
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd


def generate_insights(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Analyzes dataframe characteristics and generates 3-5 high-signal,
    plain-language, evidence-based insights.
    
    Returns:
        List of insight dictionaries with title, explanation, category, tag, and metrics.
    """
    if df is None or df.empty:
        return []

    insights: List[Dict[str, Any]] = []
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    total_rows = len(df)

    # 1. DATA QUALITY & COMPLETENESS INSIGHT
    missing_total = int(df.isnull().sum().sum())
    total_cells = total_rows * len(df.columns)
    duplicate_count = int(df.duplicated().sum())

    if missing_total > 0:
        missing_pct = round(missing_total / total_cells * 100, 1)
        worst_col = df.isnull().sum().idxmax()
        worst_col_pct = round(df[worst_col].isnull().sum() / total_rows * 100, 1)
        insights.append({
            "category": "Data Quality",
            "tag": "Warning" if worst_col_pct > 15 else "Attention",
            "title": f"Missing Values Detected ({missing_pct}% overall)",
            "explanation": (
                f"The dataset contains {missing_total:,} missing values ({missing_pct}% of total cells). "
                f"Column '{worst_col}' is the most sparse with {worst_col_pct}% missing entries, "
                f"which warrants imputation or selective filtering prior to downstream modeling."
            ),
            "metric": f"{worst_col_pct}% null in '{worst_col}'",
        })
    elif duplicate_count > 0:
        dup_pct = round(duplicate_count / total_rows * 100, 1)
        insights.append({
            "category": "Data Quality",
            "tag": "Attention",
            "title": f"Duplicate Rows Identified ({duplicate_count:,} rows)",
            "explanation": (
                f"Found {duplicate_count:,} duplicate records ({dup_pct}% of total dataset). "
                f"Deduplicating rows may prevent double-counting in statistical aggregations."
            ),
            "metric": f"{duplicate_count} duplicate rows",
        })
    else:
        insights.append({
            "category": "Data Quality",
            "tag": "Optimal",
            "title": "Clean & Complete Records",
            "explanation": (
                f"All {total_rows:,} rows across {len(df.columns)} columns are 100% complete with zero null cells "
                f"and zero duplicate rows, providing a reliable foundation for statistical inferences."
            ),
            "metric": "100% Complete",
        })

    # 2. DISTRIBUTION SKEWNESS & CENTRAL TENDENCY
    if num_cols:
        skew_candidates = []
        for col in num_cols:
            series = df[col].dropna()
            if len(series) > 5 and series.nunique() > 2:
                mean_val = float(series.mean())
                median_val = float(series.median())
                std_val = float(series.std())
                if std_val > 0 and median_val != 0:
                    skew_ratio = abs(mean_val - median_val) / (std_val + 1e-6)
                    skew_candidates.append((col, mean_val, median_val, skew_ratio))

        if skew_candidates:
            # Pick the most skewed distribution
            skew_candidates.sort(key=lambda x: x[3], reverse=True)
            top_col, mean_v, med_v, ratio = skew_candidates[0]
            pct_diff = round(abs(mean_v - med_v) / (abs(med_v) + 1e-6) * 100, 1)

            if mean_v > med_v and pct_diff > 5:
                direction = "right-skewed"
                desc = "a small cluster of high-value outliers pulls the arithmetic average up"
            elif mean_v < med_v and pct_diff > 5:
                direction = "left-skewed"
                desc = "lower-end observations pull down the mean relative to the central median"
            else:
                direction = "balanced"
                desc = "the distribution is relatively symmetrical around the central tendency"

            insights.append({
                "category": "Distribution",
                "tag": "Pattern",
                "title": f"Skewness Profile in '{top_col}'",
                "explanation": (
                    f"In '{top_col}', the mean ({mean_v:,.2f}) deviates from the median ({med_v:,.2f}) by {pct_diff}%. "
                    f"This indicates a {direction} pattern where {desc}. Median is recommended for robust benchmarking."
                ),
                "metric": f"Mean: {mean_v:,.1f} | Med: {med_v:,.1f}",
            })

    # 3. CATEGORICAL CONCENTRATION (PARETO PRINCIPLE)
    if cat_cols:
        concentration_candidates = []
        for col in cat_cols:
            series = df[col].dropna()
            val_counts = series.value_counts()
            if len(val_counts) >= 2:
                top_name = str(val_counts.index[0])
                top_count = int(val_counts.iloc[0])
                top_pct = round(top_count / len(series) * 100, 1)
                concentration_candidates.append((col, top_name, top_count, top_pct, len(val_counts)))

        if concentration_candidates:
            # Pick highest concentration
            concentration_candidates.sort(key=lambda x: x[3], reverse=True)
            c_col, top_n, top_c, top_p, num_unique = concentration_candidates[0]

            insights.append({
                "category": "Category Share",
                "tag": "Dominance" if top_p > 50 else "Concentration",
                "title": f"Category Concentration in '{c_col}'",
                "explanation": (
                    f"The dominant segment '{top_n}' represents {top_p}% ({top_c:,} of {total_rows:,} records) "
                    f"across {num_unique} distinct categories in '{c_col}'. "
                    f"{'This shows strong concentration in one primary category.' if top_p > 40 else 'Categories remain relatively distributed.'}"
                ),
                "metric": f"'{top_n}' accounts for {top_p}%",
            })

    # 4. BIVARIATE CORRELATION / ASSOCIATION
    if len(num_cols) >= 2:
        num_df = df[num_cols].dropna()
        if len(num_df) > 5:
            corr_mat = num_df.corr()
            strongest_corr = 0.0
            strongest_pair = (num_cols[0], num_cols[1])

            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    val = corr_mat.iloc[i, j]
                    if not np.isnan(val) and abs(val) > abs(strongest_corr):
                        strongest_corr = float(val)
                        strongest_pair = (num_cols[i], num_cols[j])

            if abs(strongest_corr) >= 0.35:
                direction = "positive" if strongest_corr > 0 else "negative"
                strength = "strong" if abs(strongest_corr) > 0.7 else "moderate"
                insights.append({
                    "category": "Correlation",
                    "tag": "Signal",
                    "title": f"Linear Association: {strongest_pair[0]} & {strongest_pair[1]}",
                    "explanation": (
                        f"Observed a {strength} {direction} correlation (r = {strongest_corr:.2f}) between '{strongest_pair[0]}' and '{strongest_pair[1]}'. "
                        f"Higher values in '{strongest_pair[0]}' reliably co-occur with {'higher' if strongest_corr > 0 else 'lower'} '{strongest_pair[1]}'. "
                        f"(Note: Correlation indicates association, not necessarily direct causation)."
                    ),
                    "metric": f"Pearson r = {strongest_corr:.2f}",
                })

    # 5. DOMAIN-SPECIFIC HEURISTIC EVIDENCE
    cols_lower = {c.lower(): c for c in df.columns}

    # Student domain check
    if any(k in cols_lower for k in ["math_score", "reading_score", "score"]):
        score_key = next((cols_lower[k] for k in cols_lower if "score" in k), None)
        group_key = next((cols_lower[k] for k in cols_lower if k in ["test_prep_completed", "gender", "grade_level"]), None)
        if score_key and group_key:
            grp = df.groupby(group_key)[score_key].mean().round(1)
            if len(grp) >= 2:
                top_grp = grp.idxmax()
                low_grp = grp.idxmin()
                gap = round(grp[top_grp] - grp[low_grp], 1)
                insights.append({
                    "category": "Academic Performance",
                    "tag": "Finding",
                    "title": f"Performance Gap in '{score_key}'",
                    "explanation": (
                        f"Students in group '{top_grp}' achieved an average {score_key} of {grp[top_grp]}, "
                        f"exceeding '{low_grp}' ({grp[low_grp]}) by {gap} points."
                    ),
                    "metric": f"+{gap} pts gap ({top_grp})",
                })

    # HR domain check
    elif any(k in cols_lower for k in ["salary", "compensation"]):
        sal_key = next((cols_lower[k] for k in cols_lower if "salary" in k or "comp" in k), None)
        dept_key = next((cols_lower[k] for k in cols_lower if "dept" in k or "department" in k), None)
        if sal_key and dept_key:
            grp = df.groupby(dept_key)[sal_key].median().round(0)
            if len(grp) >= 2:
                top_dept = grp.idxmax()
                insights.append({
                    "category": "Compensation",
                    "tag": "Finding",
                    "title": f"Top Paying Department: {top_dept}",
                    "explanation": (
                        f"The '{top_dept}' department has the highest median compensation at ${grp[top_dept]:,.0f}, "
                        f"while organization-wide median compensation is ${df[sal_key].median():,.0f}."
                    ),
                    "metric": f"${grp[top_dept]:,.0f} median",
                })

    # Return bounded 3 to 5 insights
    return insights[:5]
