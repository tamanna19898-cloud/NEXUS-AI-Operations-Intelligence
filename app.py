"""
NEXUS AI — Smart Data Analytics Platform
A clean, modular Streamlit application for end-to-end dataset profiling,
interactive Plotly visualizations, and evidence-based insights.
"""

from io import BytesIO
from pathlib import Path
import pandas as pd
import streamlit as st

from src.data_analyzer import (
    detect_column_types,
    detect_dataset_domain,
    get_column_profiles,
    get_dataset_overview,
    get_descriptive_stats,
    get_missing_breakdown,
)
from src.data_loader import DataLoaderError, get_sample_datasets, load_dataset
from src.insights import generate_insights
from src.visualization import (
    create_bar_chart,
    create_histogram,
    create_line_chart,
    create_scatter_plot,
    generate_recommended_visualizations,
    validate_chart_inputs,
)

# -----------------------------------------------------------------------------
# STREAMLIT PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NEXUS AI — Smart Data Analytics",
    page_icon="assets/logo.png" if Path("assets/logo.png").exists() else "📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Clean, professional SaaS typography and card styling
st.markdown(
    """
    <style>
    /* Global Clean SaaS Theme */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }
    
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Top Header Bar */
    .app-header {
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #E2E8F0;
    }
    .app-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.02em;
        margin: 0;
    }
    .app-subtitle {
        font-size: 0.95rem;
        color: #64748B;
        margin-top: 0.25rem;
    }
    
    /* KPI Metric Cards */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 0.75rem;
        padding: 1.25rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.06);
    }
    .metric-label {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 0.35rem;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.1;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #94A3B8;
        margin-top: 0.35rem;
    }
    
    /* Insight Cards */
    .insight-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #4F46E5;
        border-radius: 0.5rem;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    .insight-card-warning {
        border-left-color: #F59E0B;
    }
    .insight-card-optimal {
        border-left-color: #10B981;
    }
    .insight-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: #0F172A;
        margin-bottom: 0.3rem;
    }
    .insight-body {
        font-size: 0.85rem;
        color: #475569;
        line-height: 1.5;
        margin: 0;
    }
    .insight-tag {
        display: inline-block;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.15rem 0.5rem;
        border-radius: 9999px;
        background: #EEF2FF;
        color: #4338CA;
        margin-bottom: 0.4rem;
    }

    /* Section Headings */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }

    /* Clean file uploader container */
    [data-testid="stFileUploader"] {
        background: #FFFFFF;
        padding: 0.75rem;
        border-radius: 0.75rem;
        border: 1px dashed #CBD5E1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# DATA CACHING & SESSION STATE
# -----------------------------------------------------------------------------
if "df" not in st.session_state:
    st.session_state.df = None
if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = ""


def set_active_dataset(df: pd.DataFrame, name: str) -> None:
    st.session_state.df = df
    st.session_state.dataset_name = name


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### **NEXUS AI**")
    st.caption("Smart Data Analytics Platform")
    st.markdown("---")

    selected_page = st.radio(
        "Navigation",
        options=["1. Overview", "2. Visualizations", "3. Data Explorer"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("#### Sample Datasets")
    samples = get_sample_datasets()
    if samples:
        sample_choice = st.selectbox(
            "Quick Demo Datasets",
            options=["Select a sample..."] + list(samples.keys()),
            label_visibility="collapsed",
        )
        if sample_choice != "Select a sample...":
            try:
                sampled_df = load_dataset(samples[sample_choice])
                set_active_dataset(sampled_df, sample_choice)
                st.success(f"Loaded {sample_choice}")
            except Exception as e:
                st.error(f"Error loading sample: {e}")

    # Sidebar footer
    st.markdown("<div style='height: 120px;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.caption("NEXUS AI · v2.1.0\nModular Architecture & Clean Design")


# -----------------------------------------------------------------------------
# DATA INGESTION COMPONENT (Always accessible at top or overview)
# -----------------------------------------------------------------------------
def render_file_uploader():
    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded_file = st.file_uploader(
            "Upload your dataset (CSV or Excel)",
            type=["csv", "xlsx", "xls"],
            help="Supports standard comma, semicolon, tab CSVs and Excel workbooks.",
        )
        if uploaded_file is not None:
            if st.session_state.dataset_name != uploaded_file.name:
                try:
                    df = load_dataset(uploaded_file, uploaded_file.name)
                    set_active_dataset(df, uploaded_file.name)
                    st.success(f"Successfully loaded '{uploaded_file.name}' ({len(df):,} rows, {len(df.columns)} columns)")
                except DataLoaderError as err:
                    st.error(f"Upload error: {str(err)}")
                except Exception as err:
                    st.error(f"Unexpected error: {str(err)}")

    with col2:
        if st.session_state.df is not None:
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; padding: 0.75rem 1rem; border-radius: 0.5rem; margin-top: 1.5rem;">
                    <div style="font-size: 0.75rem; color: #64748B; font-weight: 600;">ACTIVE DATASET</div>
                    <div style="font-size: 0.9rem; font-weight: 700; color: #0F172A; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        {st.session_state.dataset_name or 'Uploaded File'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# -----------------------------------------------------------------------------
# PAGE 1: OVERVIEW
# -----------------------------------------------------------------------------
if selected_page == "1. Overview":
    st.markdown(
        """
        <div class="app-header">
            <h1 class="app-title">Understand Your Data</h1>
            <p class="app-subtitle">Upload a dataset to explore its patterns, statistics, and insights.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_file_uploader()

    df = st.session_state.df

    if df is None:
        st.info("👆 Please upload a CSV or Excel file, or pick a sample dataset from the sidebar to begin analysis.")
        # Auto-load student performance dataset for instant presentation view if empty
        if st.button("🚀 Load Demo Dataset (Student Academic Performance)"):
            samples = get_sample_datasets()
            if "Student Academic Performance" in samples:
                set_active_dataset(load_dataset(samples["Student Academic Performance"]), "Student Academic Performance")
                st.rerun()
    else:
        # Overview KPIs
        overview = get_dataset_overview(df)
        domain_info = detect_dataset_domain(df)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Total Rows</div>
                    <div class="metric-value">{overview['total_rows']:,}</div>
                    <div class="metric-sub">{overview['memory_mb']} MB in memory</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Total Columns</div>
                    <div class="metric-value">{overview['total_columns']:,}</div>
                    <div class="metric-sub">{domain_info['domain']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Missing Values</div>
                    <div class="metric-value" style="color: {'#EF4444' if overview['missing_values'] > 0 else '#10B981'};">
                        {overview['missing_values']:,}
                    </div>
                    <div class="metric-sub">{overview['missing_pct']}% of total cells</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Duplicate Rows</div>
                    <div class="metric-value" style="color: {'#F59E0B' if overview['duplicate_rows'] > 0 else '#10B981'};">
                        {overview['duplicate_rows']:,}
                    </div>
                    <div class="metric-sub">{overview['duplicate_pct']}% duplicates</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        # Columns profile and insights in 2 columns
        left_col, right_col = st.columns([5, 4])

        with left_col:
            st.markdown("<div class='section-title'>Dataset Profile</div>", unsafe_allow_html=True)
            col_types = detect_column_types(df)

            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                st.markdown(f"**Numerical Columns ({len(col_types['numerical'])})**")
                if col_types["numerical"]:
                    st.write(", ".join([f"`{c}`" for c in col_types["numerical"]]))
                else:
                    st.caption("None detected")
            with col_sub2:
                st.markdown(f"**Categorical Columns ({len(col_types['categorical'])})**")
                if col_types["categorical"]:
                    st.write(", ".join([f"`{c}`" for c in col_types["categorical"]]))
                else:
                    st.caption("None detected")

            # Column Profile Summary Table
            profiles = get_column_profiles(df)
            profile_df = pd.DataFrame(profiles)[["column_name", "category", "data_type", "missing_count", "unique_values"]]
            profile_df.columns = ["Column", "Type", "Data Type", "Missing", "Unique"]
            st.dataframe(profile_df, use_container_width=True, hide_index=True)

        with right_col:
            st.markdown("<div class='section-title'>Key Insights</div>", unsafe_allow_html=True)
            insights = generate_insights(df)

            if not insights:
                st.caption("No specific insights generated for this dataset.")
            else:
                for ins in insights:
                    tag_class = "insight-card"
                    if ins["tag"] in ["Warning", "Attention"]:
                        tag_class += " insight-card-warning"
                    elif ins["tag"] in ["Optimal"]:
                        tag_class += " insight-card-optimal"

                    st.markdown(
                        f"""
                        <div class="{tag_class}">
                            <span class="insight-tag">{ins['category']} · {ins['tag']}</span>
                            <div class="insight-title">{ins['title']}</div>
                            <p class="insight-body">{ins['explanation']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


# -----------------------------------------------------------------------------
# PAGE 2: VISUALIZATIONS
# -----------------------------------------------------------------------------
elif selected_page == "2. Visualizations":
    st.markdown(
        """
        <div class="app-header">
            <h1 class="app-title">Explore Your Data</h1>
            <p class="app-subtitle">Ask questions to generate charts on demand or build custom visual models.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = st.session_state.df

    if df is None:
        st.info("Please upload a dataset or select a sample from the sidebar to create visualizations.")
    else:
        # -----------------------------------------------------------------
        # AI CHART ASSISTANT (Natural Language to Chart)
        # -----------------------------------------------------------------
        with st.container():
            st.markdown(
                """
                <div style="background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%); padding: 1.25rem 1.5rem; border-radius: 1rem; color: #FFFFFF; margin-bottom: 1.5rem;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 0.5rem;">
                            ✨ AI Chart Assistant
                            <span style="font-size: 0.7rem; background: rgba(99, 102, 241, 0.3); border: 1px solid rgba(129, 140, 248, 0.4); color: #C7D2FE; padding: 0.15rem 0.5rem; border-radius: 9999px;">
                                English & Hindi / Hinglish Supported
                            </span>
                        </h3>
                    </div>
                    <p style="font-size: 0.85rem; color: #CBD5E1; margin: 0.35rem 0 0.75rem 0;">
                        Ask any question about this dataset (e.g., <i>"2015 me kisne sabse jyada run mare?"</i>, <i>"Kaun si team sabse jyada jiti?"</i>, <i>"Highest salary by department"</i>).
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Sample suggested chips based on columns
            cols_lower = [c.lower() for c in df.columns]
            sample_prompts = []
            if any("run" in c or "batsman" in c for c in cols_lower):
                sample_prompts = [
                    "2015 me kisne sabse jyada run mare?",
                    "Kaun si team sabse jyada match jiti hai?",
                    "Sabse jyada strike rate kiska rha hai?",
                ]
            elif any("score" in c for c in cols_lower):
                sample_prompts = [
                    "Who scored the highest in math?",
                    "Average math score by gender",
                    "Attendance rate vs scores correlation",
                ]
            elif any("salary" in c for c in cols_lower):
                sample_prompts = [
                    "Which department has highest average salary?",
                    "Top 5 highest paid job titles",
                    "Years experience vs salary",
                ]
            else:
                sample_prompts = [
                    f"Top 5 categories in {df.columns[0]}",
                    f"Highest values in {df.select_dtypes(include=['number']).columns[0] if len(df.select_dtypes(include=['number']).columns) > 0 else df.columns[0]}",
                ]

            prompt_cols = st.columns(len(sample_prompts))
            chosen_prompt = None
            for idx, p_text in enumerate(sample_prompts):
                with prompt_cols[idx]:
                    if st.button(f"💡 {p_text}", key=f"p_{idx}", use_container_width=True):
                        chosen_prompt = p_text

            nl_query = st.text_input(
                "Ask a question on this dataset:",
                value=chosen_prompt or "",
                placeholder="e.g. 2015 me kisne sabse jyada run mare? / Which team won the most?",
                key="nl_query_input",
            )

            if nl_query:
                # Query Solver
                q_clean = nl_query.lower()
                import re
                year_match = re.search(r"\b(20\d\d|19\d\d)\b", q_clean)
                target_year = year_match.group(1) if year_match else None

                working_df = df.copy()
                season_col = next((c for c in df.columns if "season" in c.lower() or "year" in c.lower()), None)
                if target_year and season_col:
                    working_df = working_df[working_df[season_col].astype(str).str.contains(target_year)]

                # Determine target columns
                target_x = df.columns[0]
                target_y = None
                agg_type = "Sum"

                if any(k in q_clean for k in ["run", "batsman", "mare", "scored"]):
                    target_x = next((c for c in df.columns if any(k in c.lower() for k in ["batsman", "player", "name"])), df.columns[0])
                    target_y = next((c for c in df.columns if "run" in c.lower() or "score" in c.lower()), None)
                elif any(k in q_clean for k in ["team", "jiti", "won", "winner", "match"]):
                    target_x = next((c for c in df.columns if any(k in c.lower() for k in ["winner", "team"])), df.columns[0])
                    agg_type = "Count"
                elif any(k in q_clean for k in ["salary", "department", "comp"]):
                    target_x = next((c for c in df.columns if "dept" in c.lower()), df.columns[0])
                    target_y = next((c for c in df.columns if "salary" in c.lower()), None)
                elif any(k in q_clean for k in ["average", "ausat", "avg"]):
                    agg_type = "Mean"
                    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
                    cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
                    target_x = cat_cols[0] if cat_cols else df.columns[0]
                    target_y = num_cols[0] if num_cols else None

                if target_y is None and len(df.select_dtypes(include=["number"]).columns) > 0:
                    target_y = df.select_dtypes(include=["number"]).columns[0]

                # Compute Aggregation
                if agg_type == "Count" or target_y is None:
                    res_series = working_df[target_x].value_counts().head(10)
                    chart_fig = create_bar_chart(working_df, x_col=target_x, agg_func="Count")
                    leader_name = res_series.index[0] if len(res_series) > 0 else "N/A"
                    leader_val = res_series.iloc[0] if len(res_series) > 0 else 0
                    answer_text = f"**Answer:** **{leader_name}** leads with **{leader_val:,} matches / entries**"
                else:
                    if agg_type == "Mean":
                        res_series = working_df.groupby(target_x)[target_y].mean().sort_values(ascending=False).head(10)
                    else:
                        res_series = working_df.groupby(target_x)[target_y].sum().sort_values(ascending=False).head(10)

                    chart_fig = create_bar_chart(working_df, x_col=target_x, y_col=target_y, agg_func=agg_type)
                    leader_name = res_series.index[0] if len(res_series) > 0 else "N/A"
                    leader_val = res_series.iloc[0] if len(res_series) > 0 else 0
                    answer_text = f"**Answer:** **{leader_name}** has the highest ({agg_type}) of **{target_y}** at **{leader_val:,.1f}**"

                if target_year:
                    answer_text += f" in year/season **{target_year}**."
                else:
                    answer_text += "."

                st.success(answer_text)
                st.plotly_chart(chart_fig, use_container_width=True)

        st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

        # Dynamic Interactive Plot Builder
        st.markdown("<div class='section-title'>Custom Chart Builder</div>", unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            chart_type = st.selectbox(
                "Chart Type",
                options=["Bar Chart", "Line Chart", "Histogram", "Scatter Plot"],
            )

        with c2:
            x_col = st.selectbox("X-Axis Column", options=list(df.columns))

        with c3:
            # Y-Axis options depending on chart type
            if chart_type in ["Line Chart", "Scatter Plot"]:
                num_cols = df.select_dtypes(include=["number"]).columns.tolist()
                y_options = num_cols if num_cols else list(df.columns)
                y_col = st.selectbox("Y-Axis Column (Numerical)", options=y_options)
            elif chart_type == "Bar Chart":
                num_cols = df.select_dtypes(include=["number"]).columns.tolist()
                y_col = st.selectbox("Y-Axis Column (Optional)", options=["None (Count Frequency)"] + num_cols)
                if y_col == "None (Count Frequency)":
                    y_col = None
            else:
                y_col = None
                st.selectbox("Y-Axis Column", options=["N/A for Histogram"], disabled=True)

        with c4:
            if chart_type == "Bar Chart" and y_col is not None:
                agg_func = st.selectbox("Aggregation", options=["Mean", "Sum", "Median", "Max", "Min"])
            else:
                agg_func = "Count"
                cat_cols = [c for c in df.columns if c not in [x_col, y_col]]
                color_col = st.selectbox("Color / Group By (Optional)", options=["None"] + cat_cols)
                color_col = None if color_col == "None" else color_col

        # Validation & Rendering
        is_valid, err_msg = validate_chart_inputs(chart_type, df, x_col, y_col)

        if not is_valid:
            st.error(f"Cannot generate chart: {err_msg}")
        else:
            try:
                if chart_type == "Bar Chart":
                    fig = create_bar_chart(df, x_col=x_col, y_col=y_col, agg_func=agg_func)
                elif chart_type == "Line Chart":
                    fig = create_line_chart(df, x_col=x_col, y_col=y_col)
                elif chart_type == "Histogram":
                    fig = create_histogram(df, x_col=x_col)
                elif chart_type == "Scatter Plot":
                    fig = create_scatter_plot(df, x_col=x_col, y_col=y_col)

                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Visualization error: {str(e)}")

        # Recommended Visualizations Section
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Recommended Automated Visualizations</div>", unsafe_allow_html=True)
        st.caption("Auto-generated based on detected column types and variance.")

        recs = generate_recommended_visualizations(df)
        if recs:
            rec_cols = st.columns(len(recs))
            for i, rec in enumerate(recs):
                with rec_cols[i]:
                    st.markdown(f"**{rec['title']}**")
                    st.caption(rec["reason"])
                    st.plotly_chart(rec["figure"], use_container_width=True)
        else:
            st.caption("Not enough columns to generate automated recommendations.")


# -----------------------------------------------------------------------------
# PAGE 3: DATA EXPLORER
# -----------------------------------------------------------------------------
elif selected_page == "3. Data Explorer":
    st.markdown(
        """
        <div class="app-header">
            <h1 class="app-title">Explore Dataset</h1>
            <p class="app-subtitle">Inspect raw records, filter columns, check missing values, and review descriptive statistics.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = st.session_state.df

    if df is None:
        st.info("Please upload a dataset or select a sample from the sidebar to inspect raw records.")
    else:
        # Search & Column Filter Bar
        f_col1, f_col2, f_col3 = st.columns([3, 3, 2])
        with f_col1:
            search_query = st.text_input("Search in dataset", placeholder="Filter records by text...")
        with f_col2:
            selected_columns = st.multiselect(
                "Filter Columns",
                options=list(df.columns),
                default=list(df.columns)[:8] if len(df.columns) > 8 else list(df.columns),
            )
        with f_col3:
            # CSV Download Button
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            st.download_button(
                label="📥 Download Clean CSV",
                data=csv_data,
                file_name=f"nexus_export_{st.session_state.dataset_name or 'data'}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        # Apply search and column filtering
        filtered_df = df.copy()
        if search_query:
            mask = filtered_df.astype(str).apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
            filtered_df = filtered_df[mask]

        if selected_columns:
            display_df = filtered_df[selected_columns]
        else:
            display_df = filtered_df

        st.caption(f"Showing {len(display_df):,} of {len(df):,} total records")
        st.dataframe(display_df, use_container_width=True)

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        # Descriptive Statistics & Missing Breakdown Tabs
        tab1, tab2 = st.tabs(["📊 Descriptive Statistics", "⚠️ Missing Values Breakdown"])

        with tab1:
            stats = get_descriptive_stats(df)
            if "numerical" in stats:
                st.markdown("**Numerical Features Summary**")
                st.dataframe(stats["numerical"], use_container_width=True, hide_index=True)
            if "categorical" in stats:
                st.markdown("**Categorical Features Summary**")
                st.dataframe(stats["categorical"], use_container_width=True, hide_index=True)
            if not stats:
                st.caption("No descriptive statistics could be calculated.")

        with tab2:
            missing_df = get_missing_breakdown(df)
            st.dataframe(missing_df, use_container_width=True, hide_index=True)
