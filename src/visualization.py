"""
NEXUS AI - Visualization Module
Creates clean, interactive Plotly visualizations with input validation
and automated chart recommendations based on column semantics.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# Professional subtle color palette
NEXUS_COLOR_SEQUENCE = [
    "#4F46E5",  # Primary Indigo
    "#06B6D4",  # Cyan
    "#10B981",  # Emerald
    "#F59E0B",  # Amber
    "#8B5CF6",  # Violet
    "#EC4899",  # Pink
    "#64748B",  # Slate
]

PLOT_TEMPLATE = "plotly_white"


def validate_chart_inputs(
    chart_type: str,
    df: pd.DataFrame,
    x_col: str,
    y_col: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Validates whether chosen columns are valid and suitable for the selected chart type.
    
    Returns:
        (is_valid: bool, error_message: str)
    """
    if df is None or df.empty:
        return False, "Dataset is empty. Cannot generate chart."

    if not x_col or x_col not in df.columns:
        return False, f"X-axis column '{x_col}' does not exist in the dataset."

    chart_type_lower = chart_type.lower()

    if chart_type_lower in ["line", "line chart", "scatter", "scatter plot"]:
        if not y_col:
            return False, f"{chart_type} requires both an X-axis and a Y-axis column."
        if y_col not in df.columns:
            return False, f"Y-axis column '{y_col}' does not exist in the dataset."
        if not pd.api.types.is_numeric_dtype(df[y_col]):
            return False, f"Y-axis for {chart_type} must be a numerical column. '{y_col}' has type '{df[y_col].dtype}'."

    if chart_type_lower in ["scatter", "scatter plot"]:
        if not pd.api.types.is_numeric_dtype(df[x_col]):
            return False, f"Scatter plot requires both X and Y to be numerical. '{x_col}' is not numeric."

    return True, ""


def create_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: Optional[str] = None,
    agg_func: str = "Count",
    color_col: Optional[str] = None,
    title: Optional[str] = None,
) -> go.Figure:
    """Creates an interactive, clean Plotly bar chart with aggregation support."""
    clean_df = df.dropna(subset=[x_col] + ([y_col] if y_col else []))

    if y_col is None or agg_func == "Count":
        grouped = clean_df[x_col].value_counts().reset_index()
        grouped.columns = [x_col, "Count"]
        # Limit top 25 categories for readability
        grouped = grouped.head(25)
        y_name = "Count"
        data_to_plot = grouped
    else:
        agg_map = {"Sum": "sum", "Mean": "mean", "Median": "median", "Max": "max", "Min": "min"}
        mapped_agg = agg_map.get(agg_func, "mean")
        grouped = clean_df.groupby(x_col)[y_col].agg(mapped_agg).reset_index()
        grouped.columns = [x_col, f"{agg_func} of {y_col}"]
        grouped = grouped.sort_values(by=grouped.columns[1], ascending=False).head(25)
        y_name = grouped.columns[1]
        data_to_plot = grouped

    chart_title = title or (f"{y_name} by {x_col}" if y_col else f"Frequency Distribution of {x_col}")

    fig = px.bar(
        data_to_plot,
        x=x_col,
        y=y_name,
        color=color_col if (color_col and color_col in data_to_plot.columns) else None,
        color_discrete_sequence=NEXUS_COLOR_SEQUENCE,
        template=PLOT_TEMPLATE,
        title=chart_title,
    )

    fig.update_layout(
        font_family="system-ui, -apple-system, sans-serif",
        title_font_size=15,
        title_font_color="#0F172A",
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(showgrid=False, linecolor="#CBD5E1", tickangle=-30 if len(str(data_to_plot[x_col].iloc[0])) > 6 else 0),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#CBD5E1"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    return fig


def create_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    title: Optional[str] = None,
) -> go.Figure:
    """Creates a clean Plotly line chart, sorting X automatically."""
    clean_df = df.dropna(subset=[x_col, y_col]).copy()

    # Try datetime or numeric conversion for clean ordering
    if not pd.api.types.is_numeric_dtype(clean_df[x_col]):
        try:
            clean_df["_x_sort"] = pd.to_datetime(clean_df[x_col])
            clean_df = clean_df.sort_values(by="_x_sort")
        except Exception:
            clean_df = clean_df.sort_values(by=x_col)
    else:
        clean_df = clean_df.sort_values(by=x_col)

    chart_title = title or f"{y_col} across {x_col}"

    fig = px.line(
        clean_df,
        x=x_col,
        y=y_col,
        color=color_col if (color_col and color_col in clean_df.columns) else None,
        color_discrete_sequence=NEXUS_COLOR_SEQUENCE,
        template=PLOT_TEMPLATE,
        title=chart_title,
        markers=True if len(clean_df) <= 40 else False,
    )

    fig.update_layout(
        font_family="system-ui, -apple-system, sans-serif",
        title_font_size=15,
        title_font_color="#0F172A",
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(showgrid=False, linecolor="#CBD5E1"),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#CBD5E1"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    return fig


def create_histogram(
    df: pd.DataFrame,
    x_col: str,
    nbins: int = 30,
    color_col: Optional[str] = None,
    title: Optional[str] = None,
) -> go.Figure:
    """Creates a distribution histogram with marginal box indicator."""
    clean_df = df.dropna(subset=[x_col])
    chart_title = title or f"Distribution of {x_col}"

    fig = px.histogram(
        clean_df,
        x=x_col,
        nbins=nbins,
        color=color_col if (color_col and color_col in clean_df.columns) else None,
        color_discrete_sequence=NEXUS_COLOR_SEQUENCE,
        template=PLOT_TEMPLATE,
        marginal="box" if pd.api.types.is_numeric_dtype(clean_df[x_col]) else None,
        title=chart_title,
    )

    fig.update_layout(
        font_family="system-ui, -apple-system, sans-serif",
        title_font_size=15,
        title_font_color="#0F172A",
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(showgrid=False, linecolor="#CBD5E1"),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#CBD5E1", title="Frequency"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    return fig


def create_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    title: Optional[str] = None,
) -> go.Figure:
    """Creates a two-variable scatter plot."""
    clean_df = df.dropna(subset=[x_col, y_col])
    chart_title = title or f"Correlation: {x_col} vs {y_col}"

    fig = px.scatter(
        clean_df,
        x=x_col,
        y=y_col,
        color=color_col if (color_col and color_col in clean_df.columns) else None,
        color_discrete_sequence=NEXUS_COLOR_SEQUENCE,
        template=PLOT_TEMPLATE,
        title=chart_title,
        opacity=0.8,
    )

    fig.update_layout(
        font_family="system-ui, -apple-system, sans-serif",
        title_font_size=15,
        title_font_color="#0F172A",
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#CBD5E1"),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#CBD5E1"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    return fig


def generate_recommended_visualizations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generates 2 to 3 contextual, high-signal automatic visualizations based on dataset columns.
    Never creates unnecessary or ungrounded charts.
    """
    recommended = []
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    # 1. Primary categorical breakdown if available
    if cat_cols:
        primary_cat = min(cat_cols, key=lambda c: abs(df[c].nunique() - 6))
        if 2 <= df[primary_cat].nunique() <= 20:
            if num_cols:
                primary_num = num_cols[0]
                fig = create_bar_chart(df, x_col=primary_cat, y_col=primary_num, agg_func="Mean")
                recommended.append({
                    "title": f"Mean {primary_num} by {primary_cat}",
                    "figure": fig,
                    "reason": f"Compares key metric '{primary_num}' across distinct '{primary_cat}' categories.",
                })
            else:
                fig = create_bar_chart(df, x_col=primary_cat, agg_func="Count")
                recommended.append({
                    "title": f"Count Distribution of {primary_cat}",
                    "figure": fig,
                    "reason": f"Shows volume distribution of the most balanced category '{primary_cat}'.",
                })

    # 2. Primary numerical distribution
    if num_cols:
        target_num = num_cols[0]
        fig = create_histogram(df, x_col=target_num)
        recommended.append({
            "title": f"Distribution of {target_num}",
            "figure": fig,
            "reason": f"Visualizes frequency distribution, skewness, and median spread for '{target_num}'.",
        })

    # 3. Two numerical correlation if available
    if len(num_cols) >= 2:
        fig = create_scatter_plot(df, x_col=num_cols[0], y_col=num_cols[1])
        recommended.append({
            "title": f"Bivariate Relationship: {num_cols[0]} vs {num_cols[1]}",
            "figure": fig,
            "reason": f"Evaluates potential linear or cluster relationship between '{num_cols[0]}' and '{num_cols[1]}'.",
        })

    return recommended[:3]
