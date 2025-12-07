import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Cohort Retention Dashboard", layout="wide")


# Load Data

df = pd.read_csv("dataset.csv")

required_cols = ["customer_id", "order_month", "acquisition_month", "cohort_index"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

# Clean datetime
df["order_month"] = pd.to_datetime(df["order_month"], utc=True).dt.tz_localize(None)
df["acquisition_month"] = pd.to_datetime(df["acquisition_month"], utc=True).dt.tz_localize(None)

# Extract acquisition year
df["acquisition_year"] = df["acquisition_month"].dt.year


# Sidebar Filter

st.sidebar.header("Filter")
years = sorted(df["acquisition_year"].unique())
year_selected = st.sidebar.selectbox("Select Acquisition Year", years)

# Hard filter (correct)
df_year = df[df["acquisition_year"] == year_selected].copy()


# Dashboard Title

st.title("Customer Cohort Retention Dashboard")
st.subheader(f"Acquisition Year: {year_selected}")


# Cohort Size

cohort_size = df_year.groupby("acquisition_month")["customer_id"].nunique()


# Pivot Table (Raw Counts)

pivot = (
    df_year.pivot_table(
        index="acquisition_month",
        columns="cohort_index",
        values="customer_id",
        aggfunc="nunique"
    )
    .fillna(0)
    .astype(int)
)

# Force pivot to only columns actually present in the year
pivot = pivot.loc[:, sorted(pivot.columns)]


# Retention (%)

retention = pivot.divide(cohort_size, axis=0).round(4) * 100


# KPI Cards

total_customers = df_year["customer_id"].nunique()
total_orders = len(df_year)
avg_order_per_cust = total_orders / total_customers if total_customers > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Customers Acquired", f"{total_customers}")
c2.metric("Total Orders", f"{total_orders}")
c3.metric("Avg Orders per Customer", f"{avg_order_per_cust:.2f}")


# Acquisition Trend Chart

acq_data = cohort_size.reset_index()
acq_data["acq_month_str"] = acq_data["acquisition_month"].dt.strftime("%Y-%m")

fig_acq = px.bar(
    acq_data,
    x="acq_month_str",
    y="customer_id",
    title="Customer Acquisition per Month",
    labels={"customer_id": "Customers", "acq_month_str": "Acquisition Month"},
)
st.plotly_chart(fig_acq, use_container_width=True)


# Retention Heatmap (Fresh Figure Every Time)

heatmap_fig = go.Figure(
    data=go.Heatmap(
        z=retention.values,
        x=retention.columns,
        y=retention.index.strftime("%Y-%m"),
        colorscale="Blues",
        text=retention.round(1),
        texttemplate="%{text}%",
        hovertemplate="Cohort %{y}<br>Month %{x}<br>Retention %{z:.1f}%<extra></extra>"
    )
)
heatmap_fig.update_layout(
    title="Retention Heatmap (%)",
    xaxis_title="Cohort Month Index",
    yaxis_title="Acquisition Month",
    height=600
)
st.plotly_chart(heatmap_fig, use_container_width=True)


# Raw Count Heatmap

count_fig = go.Figure(
    data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index.strftime("%Y-%m"),
        colorscale="Greens",
        text=pivot.astype(int),
        texttemplate="%{text}",
        hovertemplate="Cohort %{y}<br>Month %{x}<br>Customers %{z}<extra></extra>"
    )
)
count_fig.update_layout(
    title="Cohort Size Heatmap (Raw Counts)",
    xaxis_title="Cohort Month Index",
    yaxis_title="Acquisition Month",
    height=600
)
st.plotly_chart(count_fig, use_container_width=True)
