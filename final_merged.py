import pandas as pd
import numpy as np

np.random.seed(42)

states = [
    "Maharashtra","Kerala","Assam","Bihar","Uttar Pradesh",
    "West Bengal","Karnataka","Tamil Nadu","Odisha",
    "Gujarat","Rajasthan","Madhya Pradesh","Punjab",
    "Haryana","Chhattisgarh","Jharkhand","Himachal Pradesh",
    "Uttarakhand","Tripura","Manipur","Meghalaya",
    "Nagaland","Mizoram","Arunachal Pradesh",
    "Goa","Sikkim","Telangana","Andhra Pradesh"
]

years = list(range(2005, 2024))
months = list(range(1, 13))

data = []

for state in states:
    for year in years:
        for month in months:

            # Monsoon effect
            if month in [6,7,8,9]:
                rainfall = np.random.normal(300, 80)
            else:
                rainfall = np.random.normal(80, 40)

            rainfall = max(0, rainfall)

            soil_moisture = min(100, rainfall * 0.25 + np.random.normal(30,10))
            river_discharge = rainfall * np.random.uniform(2.0,3.5)

            dam_capacity = np.random.uniform(1000,8000)
            reservoir_level = min(100, rainfall * 0.3 + np.random.normal(40,10))

            elevation = np.random.uniform(5,1500)
            drainage_density = np.random.uniform(0.5,4.0)
            population_density = np.random.uniform(100,2000)
            urbanization = np.random.uniform(15,85)

            previous_rainfall = rainfall * np.random.uniform(0.7,1.3)

            # Strong Flood Logic
            flood = 0
            if (
                (rainfall > 250 and soil_moisture > 65 and reservoir_level > 80)
                or (river_discharge > 900)
                or (elevation < 50 and rainfall > 200)
            ):
                flood = 1

            data.append([
                state, year, month,
                rainfall, soil_moisture,
                river_discharge, dam_capacity,
                reservoir_level, elevation,
                drainage_density, population_density,
                urbanization, previous_rainfall,
                flood
            ])

columns = [
    "State","Year","Month",
    "Monthly_Rainfall_mm",
    "Soil_Moisture_%", 
    "River_Discharge_Cumecs",
    "Dam_Capacity_MCM",
    "Reservoir_Level_%",
    "Elevation_m",
    "Drainage_Density",
    "Population_Density",
    "Urbanization_%",
    "Previous_Month_Rainfall",
    "Flood_Occurred"
]

df = pd.DataFrame(data, columns=columns)

df.to_csv("India_Flood_Dataset.csv", index=False)

print("Dataset Created Successfully!")
print("Total Rows:", len(df))
print(df.head())