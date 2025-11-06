import pandas as pd 
import numpy as np 
df = pd.read_csv('River_lvl(1)dataset.csv') 
df.drop_duplicates() 
df['Level'] = pd.to_numeric(df['Level'],errors='coerce') 
avg_Level = df['Level'].mean() 
df['Level']=df['Level'].fillna(avg_Level) 

df['Storage'] = pd.to_numeric(df['Storage'],errors='coerce') 
avg_Storage = df['Storage'].mean() 
df['Storage'] = df['Storage'].fillna(avg_Storage) 

Level_cap = df['Level'].quantile(0.90) 
print(Level_cap) 
df['Level'] = np.where(df['Level'] > Level_cap, Level_cap, df['Level']) 
df.info()