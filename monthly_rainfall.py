import pandas as pd
import numpy as np

df = pd.read_csv('monthly_rainfall.csv')
df.drop_duplicates()

df['JAN'] = pd.to_numeric(df['JAN'],errors='coerce')
df['JAN'] = df['JAN'].fillna(df['JAN'].mean())
df['JAN'].abs()

df['FEB'] = pd.to_numeric(df['FEB'],errors='coerce')
df['FEB'] = df['FEB'].fillna(df['FEB'].mean())
df['FEB'].abs()

df['MAR'] = pd.to_numeric(df['MAR'],errors='coerce')
df['MAR'] = df['MAR'].fillna(df['MAR'].mean())
df['MAR'].abs()

df['APR'] = pd.to_numeric(df['APR'],errors='coerce')
df['APR'] = df['APR'].fillna(df['APR'].mean())
df['APR'].abs()

df['MAY'] = pd.to_numeric(df['MAY'],errors='coerce')
df['MAY'] = df['MAY'].fillna(df['MAY'].mean())
df['MAY'].abs()

df['JUN'] = pd.to_numeric(df['JUN'],errors='coerce')
df['JUN'] = df['JUN'].fillna(df['JUN'].mean())
df['JUN'].abs()

df['JUL'] = pd.to_numeric(df['JUL'],errors='coerce')
df['JUL'] = df['JUL'].fillna(df['JUL'].mean())
df['JUL'].abs()

df['AUG'] = pd.to_numeric(df['AUG'],errors='coerce')
df['AUG'] = df['AUG'].fillna(df['AUG'].mean())
df['AUG'].abs()

df['SEP'] = pd.to_numeric(df['SEP'],errors='coerce')
df['SEP'] = df['SEP'].fillna(df['SEP'].mean())
df['SEP'].abs()

df['OCT'] = pd.to_numeric(df['OCT'],errors='coerce')
df['OCT'] = df['OCT'].fillna(df['OCT'].mean())
df['OCT'].abs()

df['NOV'] = pd.to_numeric(df['NOV'],errors='coerce')
df['NOV'] = df['NOV'].fillna(df['NOV'].mean())
df['NOV'].abs()

df['DEC'] = pd.to_numeric(df['DEC'],errors='coerce')
df['DEC'] = df['DEC'].fillna(df['DEC'].mean())
df['DEC'].abs()

df['ANNUAL'] = pd.to_numeric(df['ANNUAL'],errors='coerce')
df['ANNUAL'] = df['ANNUAL'].fillna(df['ANNUAL'].mean())
df['ANNUAL'].abs()

df['JF'] = pd.to_numeric(df['JF'],errors='coerce')
df['JF'] = df['JF'].fillna(df['JF'].mean())
df['JF'].abs()

df['MAM'] = pd.to_numeric(df['MAM'],errors='coerce')
df['MAM'] = df['MAM'].fillna(df['MAM'].mean())
df['MAM'].abs()

df['JJAS'] = pd.to_numeric(df['JJAS'],errors='coerce')
df['JJAS'] = df['JJAS'].fillna(df['JJAS'].mean())
df['JJAS'].abs()

df['OND'] = pd.to_numeric(df['OND'],errors='coerce')
df['OND'] = df['OND'].fillna(df['OND'].mean())
df['OND'].abs()

df.to_csv('monthly_rainfall_cleaned.csv')

