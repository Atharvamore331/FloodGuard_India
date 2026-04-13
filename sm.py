import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🌱 Soil Moisture Analysis Dashboard")

# Load dataset
df = pd.read_csv("merged.csv")

# Convert Date column
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

# Sidebar filters
st.sidebar.header("Filters")

states = sorted(df["State Name"].unique())
selected_state = st.sidebar.selectbox("Select State", states)

state_df = df[df["State Name"] == selected_state]

districts = sorted(state_df["DistrictName"].unique())
selected_district = st.sidebar.selectbox("Select District", districts)

district_df = state_df[state_df["DistrictName"] == selected_district]

# ===============================
# 1️⃣ Time Series Trend
# ===============================

st.subheader("📈 Soil Moisture % Trend")

fig1 = px.line(
    district_df,
    x="Date",
    y="Volume Soilmoisture percentage (at 15cm)",
    title=f"Soil Moisture Trend - {selected_district}"
)

st.plotly_chart(fig1, use_container_width=True)

# ===============================
# 2️⃣ State Comparison
# ===============================

st.subheader("📊 Average Soil Moisture % by District")

avg_district = state_df.groupby("DistrictName")[
    "Volume Soilmoisture percentage (at 15cm)"
].mean().reset_index()

fig2 = px.bar(
    avg_district,
    x="DistrictName",
    y="Volume Soilmoisture percentage (at 15cm)",
    title="Average Soil Moisture % per District"
)

st.plotly_chart(fig2, use_container_width=True)

# ===============================
# 3️⃣ Boxplot Distribution
# ===============================

st.subheader("📦 Soil Moisture Distribution")

fig3 = px.box(
    state_df,
    x="DistrictName",
    y="Volume Soilmoisture percentage (at 15cm)",
    title="Soil Moisture Distribution by District"
)

st.plotly_chart(fig3, use_container_width=True)

# ===============================
# 4️⃣ Heatmap
# ===============================

st.subheader("🔥 Soil Moisture Heatmap")

heatmap_df = district_df.pivot_table(
    index=district_df["Date"].dt.month,
    values="Volume Soilmoisture percentage (at 15cm)",
    aggfunc="mean"
)

fig4 = px.imshow(
    heatmap_df,
    labels=dict(x="Metric", y="Month", color="Moisture %"),
    aspect="auto"
)

st.plotly_chart(fig4, use_container_width=True)

# ===============================
# 5️⃣ Correlation Scatter
# ===============================

st.subheader("🔍 Correlation Analysis")

fig5 = px.scatter(
    district_df,
    x="Average SoilMoisture Volume (at 15cm)",
    y="Volume Soilmoisture percentage (at 15cm)",
    title="Volume vs Percentage Correlation",
    trendline="ols"
)

st.plotly_chart(fig5, use_container_width=True)
