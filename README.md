# NEXUS AI — Smart Data Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-3F4F75.svg)](https://plotly.com/)
[![Tests](https://img.shields.io/badge/Pytest-20%2F20%20Passing-success.svg)](https://pytest.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A clean, modular, and reliable data analytics application designed to help users upload any CSV or Excel dataset and instantly extract statistical summaries, interactive visualizations, and evidence-based insights.

Built with a **simplified, interview-ready architecture**: no bloated enterprise infrastructure, no fake mock APIs, and no hallucinations. Every number and insight is computed directly from actual data.

---

## 🎯 Core Purpose & Workflow

```text
Upload Dataset (CSV / Excel)
            ↓
  Analyze Dataset (Data Quality & Profile)
            ↓
  View Statistics (Descriptive & Missing)
            ↓
Explore Visualizations (Dynamic Plotly Builder)
            ↓
  Discover Insights (Grounded Evidence Findings)
```

### Domain-Agnostic Design
Unlike generic business templates that assume every dataset contains "sales", "revenue", or "orders", **NEXUS AI** intelligently adapts to whatever dataset is uploaded:
- **Student Performance:** Exam scores, study hours, attendance, test preparation gaps.
- **Employee & HR:** Department compensation, experience, performance ratings, attrition risk.
- **Retail & E-Commerce:** Order values, margins, discounts, category revenue.
- **Hospitality & Lodging:** Booking lead times, cancellation rates, stay duration, average daily rates (ADR).
- **General Tabular Data:** Pure statistical profiling, distribution skewness, outliers, and correlations.

---

## 📁 Project Architecture

```text
NEXUS-AI-Operations-Intelligence/
│
├── app.py                      # Main Streamlit application with 3 clean pages
├── requirements.txt            # Minimal, production-tested Python dependencies
├── conftest.py                 # Pytest root configuration
├── README.md                   # Comprehensive documentation and interview guide
├── .gitignore                  # Clean Python and OS gitignore
│
├── src/                        # Modular core library
│   ├── __init__.py             # Package initializer (v2.1.0)
│   ├── data_loader.py          # Defensive CSV/Excel ingestion & error handling
│   ├── data_analyzer.py        # Statistical summaries, column profiling & domain detection
│   ├── visualization.py        # Plotly chart generation, type validation & auto recommendations
│   └── insights.py             # 100% evidence-based, grounded statistical insights
│
├── tests/                      # Automated test suite (20 unit tests)
│   ├── __init__.py
│   ├── test_data_loader.py     # Ingestion tests (empty files, invalid formats, buffers)
│   ├── test_data_analyzer.py   # Statistical profiling & missing value assertions
│   └── test_visualization.py   # Plotly chart validation and insight integrity
│
├── sample_datasets/            # Pre-loaded sample datasets for instant demonstration
│   ├── student_performance.csv
│   ├── employee_salaries.csv
│   ├── retail_sales.csv
│   └── hospitality_bookings.csv
│
├── assets/                     # Brand visual assets
│   ├── logo.png
│   └── nexus_logo.svg
│
└── docs/                       # Visual documentation & screenshots
    └── screenshots/
```

---

## ⚙️ Technology Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Standard data science ecosystem |
| **Frontend UI** | Streamlit | Rapid, native Python reactive interface with custom clean CSS |
| **Data Engine** | Pandas & NumPy | High-performance tabular transformation and profiling |
| **Visualizations**| Plotly Express & Graph Objects | Fully interactive, zoomable, hoverable charts |
| **File Formats** | OpenPyXL & CSV engine | Robust parsing of `.csv`, `.xlsx`, and `.xls` |
| **Testing** | Pytest | 20 unit tests covering edge cases, missing data, and invalid inputs |

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/AnujDikshit/NEXUS-AI-Operations-Intelligence.git
cd NEXUS-AI-Operations-Intelligence
```

### 2. Create a Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Unit Test Suite
```bash
pytest -v
```
*Expected: 20 passed unit tests.*

### 5. Launch the Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🖥️ Application Pages

### 1. Overview (`Understand Your Data`)
- **Drag-and-drop file uploader** supporting `.csv`, `.xlsx`, and `.xls`.
- **4 Compact KPI Cards:**
  - `Total Rows` (with in-memory footprint)
  - `Total Columns` (with auto-detected dataset domain)
  - `Missing Values` (count & % of total cells)
  - `Duplicate Rows` (count & % of dataset)
- **Dataset Profile Table:** Lists column names, detected data categories (Numeric, Categorical, DateTime, Boolean), exact dtype, null counts, and sample values.
- **Key Insights:** 3 to 5 clear, evidence-based sentences explaining skewness, categorical concentration (Pareto principle), linear associations, and domain-specific comparisons.

### 2. Visualizations (`Explore Your Data`)
- **Interactive Chart Builder:**
  - Bar Charts (with dynamic aggregations: Count, Sum, Mean, Median, Min, Max)
  - Line Charts (with automated chronological or numerical sorting)
  - Histograms (with marginal box plots for distribution spread)
  - Scatter Plots (bivariate correlation analysis)
- **Defensive Type Validation:** Blocks invalid combinations (e.g. categorical axes on scatter plots) and presents actionable hints instead of crashing.
- **Automated Recommendations:** Surfaces 2–3 high-signal charts automatically based on detected column variance and data types.

### 3. Data Explorer (`Explore Dataset`)
- **Full Interactive Data Table** with responsive scrolling and pagination.
- **Global Text Search:** Filter rows instantly across all columns.
- **Column Visibility Selector:** Toggle specific features to focus on relevant variables.
- **Descriptive Statistics:** Comprehensive summary (Count, Mean, Std, Min, 25%, 50%, 75%, Max for numbers; Count, Unique, Top, Freq for categories).
- **Missing Values Breakdown:** Ranked table showing data sparsity per column.
- **Clean CSV Export:** 1-click download of the dataset.

---

## 🧪 Testing & Reliability

The test suite covers:
1. **Defensive Ingestion:** Handling zero-byte files, non-existent paths, unsupported formats (`.pdf`, `.txt`), and corrupted CSV delimiters.
2. **Data Profiling:** Verifying metric computations (row counts, null sums, duplicate checks, memory profiling).
3. **Column Type Classification:** Distinguishing numeric, categorical, and datetime strings.
4. **Visualization Validation:** Ensuring chart generators reject incompatible data types gracefully.
5. **Insights Grounding:** Guaranteeing insight generators produce non-empty, mathematically valid summaries without hallucinations.

Run tests at any time:
```bash
pytest
```

---

## 💼 Interview Talking Points & Design Decisions

When presenting this project to recruiters or technical interviewers, highlight these practical engineering choices:

1. **Why simplify from the original repository?**
   - *Previous state:* Over-engineered microservice architecture with hardcoded FastAPI endpoints (`http://127.0.0.1:8000/kpis`), mock e-commerce database dependencies, and tight coupling that failed if backend services were offline.
   - *Refactored state:* Self-contained, modular library with zero external API dependencies. Highly testable, faster to launch, and works reliably with **any** tabular dataset.
2. **Evidence-Based Insights vs. Hallucinated AI:**
   - Rather than sending sensitive data to paid third-party LLMs that can hallucinate metrics, NEXUS AI computes verifiable mathematical properties (Pearson r, Tukey IQR, skewness ratios, Pareto shares) and translates them into crisp human sentences.
3. **Defensive Column Typing:**
   - Real-world CSVs often store dates or numbers as raw strings. The data loader and analyzer normalize column names, sniff formats, and safeguard chart generation against type errors.
4. **Single Responsibility Principle (SRP):**
   - Each module in `src/` has a single clear purpose: ingestion (`data_loader.py`), statistical computation (`data_analyzer.py`), plotting (`visualization.py`), and qualitative narrative (`insights.py`).

---

## 🔮 Future Enhancements
- Exportable PDF summary reports.
- Automated missing-value imputation options (Mean/Median/KNN).
- Time-series seasonality decomposition (STL) when timestamp columns exist.

---

**Author:** Anuj Dikshit  
**License:** Apache 2.0
