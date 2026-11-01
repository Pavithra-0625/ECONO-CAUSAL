 
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="EconoCausal Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- COMPACT DESIGN ----------------
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0.5rem;
        max-width: 1500px;
    }
    h1 {font-size: 27px !important; padding-bottom: 0px;}
    h2 {font-size: 19px !important; padding-bottom: 0px;}
    h3 {font-size: 16px !important;}
    [data-testid="stMetric"] {
        background: #f3f6fb;
        padding: 10px;
        border-radius: 9px;
        border: 1px solid #e0e6ef;
    }
    [data-testid="stMetricValue"] {
        font-size: 23px;
    }
    [data-testid="stPlotlyChart"] {
        margin-bottom: -15px;
    }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
header1, header2 = st.columns([4, 1])

with header1:
    st.title("📊 EconoCausal")
    st.caption("Dynamic Pricing | Causal Machine Learning Dashboard")

with header2:
    st.caption("CAMPAIGN ANALYTICS")
    st.caption("EconML • Double Machine Learning")

st.divider()

# ---------------- DATA LOADING ----------------
uploaded_file = st.file_uploader(
    "Upload EconML results CSV",
    type=["csv"],
    label_visibility="collapsed"
)

if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    file_path = Path(__file__).parent / "outputs" / "econml_effect_estimates.csv"

    if not file_path.exists():
        st.warning("Please upload econml_effect_estimates.csv.")
        st.stop()

    df = pd.read_csv(file_path)

# ---------------- VALIDATION ----------------
required = [
    "person",
    "treatment_discount",
    "outcome_completed",
    "estimated_treatment_effect"
]

missing = [col for col in required if col not in df.columns]

if missing:
    st.error(f"Missing columns: {missing}")
    st.stop()

for col in required[1:]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=required).copy()

if df.empty:
    st.error("No valid data available.")
    st.stop()

df["Treatment"] = df["treatment_discount"].map({
    0: "BOGO",
    1: "Discount"
})

# ---------------- CUSTOMER DATA ----------------
customers = (
    df.groupby("person", as_index=False)
    .agg(
        estimated_treatment_effect=(
            "estimated_treatment_effect", "mean"
        ),
        total_offers=("person", "size")
    )
)

# ---------------- FILTERS AND BUDGET ----------------
with st.expander("⚙️ Campaign filters and budget", expanded=False):
    f1, f2, f3 = st.columns(3)

    if "age" in df.columns:
        age_values = pd.to_numeric(df["age"], errors="coerce")
        min_age = int(age_values.min())
        max_age = int(age_values.max())
        with f1:
            age_range = st.slider(
                "Age range",
                min_value=min_age,
                max_value=max_age,
                value=(min_age, max_age)
            )
        df = df[
            age_values.between(age_range[0], age_range[1])
        ].copy()

    if "gender" in df.columns:
        with f2:
            genders = st.multiselect(
                "Gender",
                sorted(df["gender"].dropna().astype(str).unique()),
                default=sorted(df["gender"].dropna().astype(str).unique())
            )
        df = df[df["gender"].astype(str).isin(genders)].copy()

    with f3:
        budget = st.number_input(
            "Marketing budget (₹)",
            min_value=0,
            value=10000,
            step=500
        )

if df.empty:
    st.warning("No records match the selected filters.")
    st.stop()

customers = (
    df.groupby("person", as_index=False)
    .agg(
        estimated_treatment_effect=(
            "estimated_treatment_effect", "mean"
        ),
        total_offers=("person", "size")
    )
)

# ---------------- KPI CARDS ----------------
st.subheader("Campaign Overview")

total_customers = len(customers)
average_ite = customers["estimated_treatment_effect"].mean()
positive_customers = (
    customers["estimated_treatment_effect"] > 0
).sum()
positive_percentage = (
    positive_customers / total_customers * 100
)

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Customers", f"{total_customers:,}")
k2.metric("Average Estimated ITE", f"{average_ite * 100:.2f}%")
k3.metric("Positive ITE Customers", f"{positive_customers:,}")
k4.metric("Positive ITE Share", f"{positive_percentage:.1f}%")

# ---------------- TWO-COLUMN CHARTS ----------------
st.divider()

left, right = st.columns(2)

with left:
    st.subheader("1. ITE Distribution")

    fig1 = px.histogram(
        customers,
        x="estimated_treatment_effect",
        nbins=25,
        labels={
            "estimated_treatment_effect": "Estimated ITE"
        }
    )

    fig1.update_layout(
        template="plotly_white",
        height=250,
        margin=dict(l=15, r=15, t=15, b=35),
        showlegend=False
    )

    st.plotly_chart(
        fig1,
        use_container_width=True,
        config={"displayModeBar": False}
    )

with right:
    st.subheader("2. BOGO vs Discount")

    comparison = (
        df.groupby("Treatment", observed=True)
        .agg(
            completion_rate=("outcome_completed", "mean"),
            total_offers=("outcome_completed", "size")
        )
        .reset_index()
    )

    comparison["completion_rate"] *= 100

    fig2 = px.bar(
        comparison,
        x="Treatment",
        y="completion_rate",
        text="completion_rate",
        labels={"completion_rate": "Completion Rate (%)"}
    )

    fig2.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig2.update_layout(
        template="plotly_white",
        height=250,
        margin=dict(l=15, r=15, t=15, b=35),
        yaxis_range=[
            0,
            max(60, comparison["completion_rate"].max() + 10)
        ],
        showlegend=False
    )

    st.plotly_chart(
        fig2,
        use_container_width=True,
        config={"displayModeBar": False}
    )

st.caption(
    "Observed completion rates are descriptive comparisons, "
    "not causal treatment effects."
)

# ---------------- CUSTOMER INSIGHTS ----------------
st.divider()

left2, right2 = st.columns([1, 1.3])

with left2:
    st.subheader("3. Customer Segments")

    customers["Segment"] = np.where(
        customers["estimated_treatment_effect"] > 0,
        "Positive ITE",
        "Zero / Negative ITE"
    )

    segment_data = (
        customers["Segment"]
        .value_counts()
        .rename_axis("Segment")
        .reset_index(name="Customers")
    )

    fig3 = px.pie(
        segment_data,
        names="Segment",
        values="Customers",
        hole=0.55
    )

    fig3.update_layout(
        template="plotly_white",
        height=235,
        margin=dict(l=5, r=5, t=5, b=5),
        legend=dict(orientation="h", y=-0.1)
    )

    st.plotly_chart(
        fig3,
        use_container_width=True,
        config={"displayModeBar": False}
    )

with right2:
    st.subheader("4. High-Potential Customers")

    top_customers = customers.nlargest(
        5, "estimated_treatment_effect"
    ).copy()


top_customers["Customer ID"] = (
    top_customers["person"].astype(str).str[:10] + "..."
)

top_customers["Estimated ITE (%)"] = (
    top_customers["estimated_treatment_effect"] * 100
).round(2)

display_table = top_customers[
    ["Customer ID", "total_offers", "Estimated ITE (%)"]
].rename(columns={
    "total_offers": "Offers"
})

st.dataframe(
    display_table,
    use_container_width=True,
    hide_index=True,
    height=205,
    column_config={
        "Customer ID": st.column_config.TextColumn(
            "Customer ID",
            width="large"
        ),
        "Offers": st.column_config.NumberColumn(
            "Offers",
            width="small"
        ),
        "Estimated ITE (%)": st.column_config.NumberColumn(
            "Estimated ITE (%)",
            format="%.2f%%",
            width="medium"
        )
    }
)

    
# ---------------- BUDGET SUMMARY ----------------
st.divider()

b1, b2, b3 = st.columns(3)

b1.metric("Available Budget", f"₹{budget:,.0f}")
b2.metric("Customers with Positive ITE", f"{positive_customers:,}")
b3.metric("Customer Records Analysed", f"{len(df):,}")

st.info(
    "Budget allocation is not yet optimized. "
    "SciPy-based personalized offer allocation will be integrated "
    "as a separate optimization module."
)

# ---------------- DOWNLOAD ----------------
download_csv = customers.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇ Download Customer ITE Results",
    data=download_csv,
    file_name="customer_ite_analysis.csv",
    mime="text/csv"
)

st.caption(
    "EconoCausal | Dynamic Pricing Using Double Machine Learning"
)
