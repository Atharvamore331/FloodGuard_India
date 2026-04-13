import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv("flood_waterbodies_dataset.csv")

df = df.drop_duplicates()

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"])

numeric_cols = [
    "Latitude","Longitude","Elevation_m",
    "Full_Reservoir_Level_m","Maximum_Water_Level_m",
    "Dead_Storage_Level_m","Live_Capacity_MCM",
    "Gross_Capacity_MCM","Catchment_Area_km2",
    "Current_Water_Level_m","Current_Storage_MCM",
    "Inflow_Cumecs","Outflow_Cumecs",
    "Rainfall_mm","River_Discharge_Cumecs",
    "Soil_Moisture_Percentage","Capacity_Utilization_Percent"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

for col in numeric_cols:
    df = df[df[col] >= 0]

df.loc[
    df["Current_Water_Level_m"] >= df["Maximum_Water_Level_m"],
    "Flood_Status"
] = "Severe"

df.loc[
    (df["Current_Water_Level_m"] >= df["Full_Reservoir_Level_m"]) &
    (df["Current_Water_Level_m"] < df["Maximum_Water_Level_m"]),
    "Flood_Status"
] = "Warning"

df["Capacity_Utilization_Percent"] = (
    df["Current_Water_Level_m"] /
    df["Full_Reservoir_Level_m"]
) * 100

df = df[df["Soil_Moisture_Percentage"] <= 100]

df = df.sort_values(["Waterbody_Name", "Date"])

df.to_csv("cleaned_flood_waterbodies_dataset.csv", index=False)