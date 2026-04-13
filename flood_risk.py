import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler


df = pd.read_csv("flood_risk_dataset_india.csv")

print("Original Shape:", df.shape)
print(df.head())

df.drop_duplicates(inplace=True)




num_cols = df.select_dtypes(include=np.number).columns
df[num_cols] = df[num_cols].fillna(df[num_cols].median())

cat_cols = df.select_dtypes(include='object').columns
for col in cat_cols:
    df[col].fillna(df[col].mode()[0], inplace=True)

for col in num_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    
    df = df[(df[col] >= lower) & (df[col] <= upper)]

le = LabelEncoder()

for col in cat_cols:
    df[col] = le.fit_transform(df[col])

scaler = StandardScaler()

X = df.drop("Flood Occurred", axis=1)
y = df["Flood  Occurred"]

X_scaled = scaler.fit_transform(X)

X_scaled = pd.DataFrame(X_scaled, columns=X.columns)


cleaned_df = pd.concat([X_scaled, y.reset_index(drop=True)], axis=1)



cleaned_df.to_csv("cleaned_flood_dataset.csv", index=False)