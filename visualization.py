import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("📊 Historical Rainfall Analysis Dashboard")

# Load dataset
df = pd.read_csv("monthly_rainfall.csv")

# Remove rows with missing YEAR
df = df.dropna(subset=["YEAR"])

# Convert YEAR to int
df["YEAR"] = df["YEAR"].astype(int)

# Subdivision Selection
subdivisions = sorted(df["SUBDIVISION"].unique())
selected_subdivision = st.selectbox("Select Subdivision", subdivisions)

sub_df = df[df["SUBDIVISION"] == selected_subdivision]

# Year Selection (Dynamic)
years = sorted(sub_df["YEAR"].unique())
selected_year = st.selectbox("Select Year", years)

year_df = sub_df[sub_df["YEAR"] == selected_year]

# ==============================
# 1️⃣ Monthly Rainfall Graph
# ==============================

st.subheader("🌧 Monthly Rainfall")

months = ["JAN","FEB","MAR","APR","MAY","JUN",
          "JUL","AUG","SEP","OCT","NOV","DEC"]

monthly_values = year_df[months].values.flatten()

fig1 = px.line(
    x=months,
    y=monthly_values,
    markers=True,
    title=f"Monthly Rainfall - {selected_subdivision} ({selected_year})"
)
fig1.update_layout(xaxis_title="Month", yaxis_title="Rainfall (mm)")
st.plotly_chart(fig1, use_container_width=True)

# ==============================
# 2️⃣ Annual Trend + Moving Avg
# ==============================

st.subheader("📈 Annual Rainfall Trend")

trend_df = sub_df.sort_values("YEAR")
trend_df["5yr_MA"] = trend_df["ANNUAL"].rolling(window=5).mean()

fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=trend_df["YEAR"],
    y=trend_df["ANNUAL"],
    mode="lines",
    name="Annual Rainfall"
))
fig2.add_trace(go.Scatter(
    x=trend_df["YEAR"],
    y=trend_df["5yr_MA"],
    mode="lines",
    name="5-Year Moving Avg"
))

fig2.update_layout(
    title="Annual Rainfall Trend with 5-Year Moving Average",
    xaxis_title="Year",
    yaxis_title="Rainfall (mm)"
)

st.plotly_chart(fig2, use_container_width=True)

# ==============================
# 3️⃣ Seasonal Comparison
# ==============================

st.subheader("🌦 Seasonal Rainfall Comparison")

seasons = ["JF", "MAM", "JJAS", "OND"]
season_values = year_df[seasons].values.flatten()

fig3 = px.bar(
    x=seasons,
    y=season_values,
    title=f"Seasonal Rainfall - {selected_subdivision} ({selected_year})"
)
fig3.update_layout(xaxis_title="Season", yaxis_title="Rainfall (mm)")
st.plotly_chart(fig3, use_container_width=True)

# ==============================
# 4️⃣ Heatmap (Year vs Month)
# ==============================

st.subheader("🔥 Rainfall Heatmap (Year vs Month)")

heatmap_df = sub_df.pivot_table(
    index="YEAR",
    values=months
)

fig4 = px.imshow(
    heatmap_df,
    labels=dict(x="Month", y="Year", color="Rainfall"),
    aspect="auto",
    title="Rainfall Heatmap"
)

st.plotly_chart(fig4, use_container_width=True)

# ==============================
# 5️⃣ Extreme Rainfall Detection
# ==============================

st.subheader("⚠ Extreme Rainfall Years")

mean_rain = trend_df["ANNUAL"].mean()
std_rain = trend_df["ANNUAL"].std()

extreme_years = trend_df[trend_df["ANNUAL"] > (mean_rain + std_rain)]

st.write(f"Mean Annual Rainfall: {round(mean_rain,2)} mm")
st.write(f"Standard Deviation: {round(std_rain,2)} mm")

if not extreme_years.empty:
    st.write("### 🌊 Extreme Rainfall Years (Above Mean + 1 Std Dev)")
    st.dataframe(extreme_years[["YEAR", "ANNUAL"]])
else:
    st.write("No extreme rainfall years detected.")
