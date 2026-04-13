import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


st.set_page_config(layout="wide")
st.title("🌊 Reservoir Level & Storage Analysis Dashboard")


df = pd.read_csv("River_lvl_cleaned.csv")


df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

# Sidebar Filters
st.sidebar.header("Filters")

reservoirs = sorted(df["Reservoir_name"].unique())
selected_reservoir = st.sidebar.selectbox("Select Reservoir", reservoirs)

res_df = df[df["Reservoir_name"] == selected_reservoir].sort_values("Date")

#  Reservoir Water Level Trend

st.subheader("📈 Reservoir Water Level Trend")

fig1 = px.line(
    res_df,
    x="Date",
    y="Level",
    title=f"Water Level Trend - {selected_reservoir}"
)

st.plotly_chart(fig1, width="stretch")

# 2️⃣ Storage Trend

st.subheader("💧 Storage Trend")

fig2 = px.line(
    res_df,
    x="Date",
    y="Storage",
    title="Storage Over Time"
)

st.plotly_chart(fig2, width="stretch")

# FRL vs Current Level Comparison

st.subheader("🏗 Full Reservoir Level (FRL) Comparison")

fig3 = go.Figure()

fig3.add_trace(go.Scatter(
    x=res_df["Date"],
    y=res_df["Level"],
    mode="lines",
    name="Current Level"
))

fig3.add_trace(go.Scatter(
    x=res_df["Date"],
    y=res_df["Full_reservoir_level"],
    mode="lines",
    name="Full Reservoir Level (FRL)"
))

fig3.update_layout(
    title="Current Level vs FRL",
    xaxis_title="Date",
    yaxis_title="Water Level"
)

st.plotly_chart(fig3, width="stretch")

#  Monthly Average Level

st.subheader("📅 Monthly Average Water Level")

monthly_avg = res_df.groupby("Month")["Level"].mean().reset_index()

fig4 = px.bar(
    monthly_avg,
    x="Month",
    y="Level",
    title="Average Monthly Water Level"
)

st.plotly_chart(fig4, width="stretch")

#  Storage vs Level Correlation

st.subheader("🔍 Storage vs Water Level Correlation")

fig5 = px.scatter(
    res_df,
    x="Storage",
    y="Level",
    title="Storage vs Water Level"
)

st.plotly_chart(fig5, width="stretch")
