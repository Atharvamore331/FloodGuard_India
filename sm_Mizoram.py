import pandas as pd
import numpy as np

df = pd.read_excel('sm_Mizoram_2020.csv.xlsx')
df.info()

vol_sm_lower = df['Volume Soilmoisture percentage (at 15cm)'].quantile(0.10)
df['Volume Soilmoisture percentage (at 15cm)'] = np.where(df['Volume Soilmoisture percentage (at 15cm)'] < vol_sm_lower, vol_sm_lower, df['Volume Soilmoisture percentage (at 15cm)'])
vol_sm_upper = df['Volume Soilmoisture percentage (at 15cm)'].quantile(0.90)
df['Volume Soilmoisture percentage (at 15cm)'] = np.where(df['Volume Soilmoisture percentage (at 15cm)'] > vol_sm_upper, vol_sm_upper, df['Volume Soilmoisture percentage (at 15cm)'])

sm_lvl_lower = df['Average Soilmoisture Level (at 15cm)'].quantile(0.10)
df['Average Soilmoisture Level (at 15cm)'] = np.where(df['Average Soilmoisture Level (at 15cm)'] < sm_lvl_lower, sm_lvl_lower, df['Average Soilmoisture Level (at 15cm)'])
sm_lvl_upper = df['Average Soilmoisture Level (at 15cm)'].quantile(0.90)
df['Average Soilmoisture Level (at 15cm)'] = np.where(df['Average Soilmoisture Level (at 15cm)'] > sm_lvl_upper, sm_lvl_upper, df['Average Soilmoisture Level (at 15cm)'])

sm_vol_lower = df['Average SoilMoisture Volume (at 15cm)'].quantile(0.10)
df['Average SoilMoisture Volume (at 15cm)'] = np.where(df['Average SoilMoisture Volume (at 15cm)'] < sm_vol_lower, sm_vol_lower, df['Average SoilMoisture Volume (at 15cm)'])
sm_vol_upper = df['Average SoilMoisture Volume (at 15cm)'].quantile(0.90)
df['Average SoilMoisture Volume (at 15cm)'] = np.where(df['Average SoilMoisture Volume (at 15cm)'] > sm_vol_upper, sm_vol_upper, df['Average SoilMoisture Volume (at 15cm)'])

sm_vol_lower = df['Aggregate Soilmoisture Percentage (at 15cm)'].quantile(0.10)
df['Aggregate Soilmoisture Percentage (at 15cm)'] = np.where(df['Aggregate Soilmoisture Percentage (at 15cm)'] < sm_vol_lower, sm_vol_lower, df['Aggregate Soilmoisture Percentage (at 15cm)'])
sm_vol_upper = df['Aggregate Soilmoisture Percentage (at 15cm)'].quantile(0.90)
df['Aggregate Soilmoisture Percentage (at 15cm)'] = np.where(df['Aggregate Soilmoisture Percentage (at 15cm)'] > sm_vol_upper, sm_vol_upper, df['Aggregate Soilmoisture Percentage (at 15cm)'])

df.to_excel('sm_Mizoram_2020_cleaned.csv.xlsx')