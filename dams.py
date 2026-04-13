import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Flood Monitoring Dashboard", layout="wide")

# ==============================================
# Load Dataset
# ==============================================
@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_flood_waterbodies_dataset.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    return df

df = load_data()

st.title("🌊 Flood Monitoring & Waterbody Dashboard")

# ==============================================
# Sidebar Filters
# ==============================================
st.sidebar.header("Filter Options")

waterbody = st.sidebar.selectbox(
    "Select Waterbody",
    df["Waterbody_Name"].unique()
)

filtered_df = df[df["Waterbody_Name"] == waterbody]

date_range = st.sidebar.date_input(
    "Select Date Range",
    [filtered_df["Date"].min(), filtered_df["Date"].max()]
)

filtered_df = filtered_df[
    (filtered_df["Date"] >= pd.to_datetime(date_range[0])) &
    (filtered_df["Date"] <= pd.to_datetime(date_range[1]))
]

# ==============================================
# Water Level Trend
# ==============================================
st.subheader("📈 Water Level Trend")

fig1, ax1 = plt.subplots()
ax1.plot(filtered_df["Date"], filtered_df["Current_Water_Level_m"])
ax1.set_xlabel("Date")
ax1.set_ylabel("Water Level (m)")
ax1.set_title("Water Level Over Time")
st.pyplot(fig1)

# ==============================================
# Storage Trend
# ==============================================
st.subheader("💧 Storage Trend")

fig2, ax2 = plt.subplots()
ax2.plot(filtered_df["Date"], filtered_df["Current_Storage_MCM"])
ax2.set_xlabel("Date")
ax2.set_ylabel("Storage (MCM)")
ax2.set_title("Storage Over Time")
st.pyplot(fig2)

# ==============================================
# Rainfall Trend
# ==============================================
st.subheader("🌧 Rainfall Trend")

fig3, ax3 = plt.subplots()
ax3.bar(filtered_df["Date"], filtered_df["Rainfall_mm"])
ax3.set_xlabel("Date")
ax3.set_ylabel("Rainfall (mm)")
st.pyplot(fig3)

# ==============================================
# Inflow vs Outflow
# ==============================================
st.subheader("🔄 Inflow vs Outflow")

fig4, ax4 = plt.subplots()
ax4.plot(filtered_df["Date"], filtered_df["Inflow_Cumecs"], label="Inflow")
ax4.plot(filtered_df["Date"], filtered_df["Outflow_Cumecs"], label="Outflow")
ax4.legend()
ax4.set_xlabel("Date")
ax4.set_ylabel("Flow (Cumecs)")
st.pyplot(fig4)

# ==============================================
# River Discharge
# ==============================================
st.subheader("🌊 River Discharge")

fig5, ax5 = plt.subplots()
ax5.plot(filtered_df["Date"], filtered_df["River_Discharge_Cumecs"])
ax5.set_xlabel("Date")
ax5.set_ylabel("Discharge (Cumecs)")
st.pyplot(fig5)

# ==============================================
# Soil Moisture
# ==============================================
st.subheader("🌱 Soil Moisture Trend")

fig6, ax6 = plt.subplots()
ax6.plot(filtered_df["Date"], filtered_df["Soil_Moisture_Percentage"])
ax6.set_xlabel("Date")
ax6.set_ylabel("Soil Moisture (%)")
st.pyplot(fig6)

# ==============================================
# Flood Status Distribution
# ==============================================
st.subheader("⚠ Flood Status Distribution")

status_counts = filtered_df["Flood_Status"].value_counts()

fig7, ax7 = plt.subplots()
ax7.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%')
st.pyplot(fig7)

# ==============================================
# Data Table
# ==============================================
st.subheader("📋 Dataset Preview")
st.dataframe(filtered_df)