import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report

# ------------------------------------------------
# 1️⃣ LOAD DATA
# ------------------------------------------------

df = pd.read_csv("cleaned_flood_dataset.csv")
df.columns = df.columns.str.strip()

if "Flood Occurred" not in df.columns:
    print("Available columns:", df.columns)
    raise ValueError("Flood Occurred column missing!")

# ------------------------------------------------
# 2️⃣ PREPARE DATA
# ------------------------------------------------

df = df.dropna(subset=["Flood Occurred"])

X = df.drop(columns=["Flood Occurred"])
y = df["Flood Occurred"]

# Fill missing values
imputer = SimpleImputer(strategy="median")
X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)

# ------------------------------------------------
# 3️⃣ TRAIN MODEL
# ------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=400,
    max_depth=20,
    class_weight="balanced",
    random_state=42
)

model.fit(X_train, y_train)

# Accuracy
y_pred = model.predict(X_test)
print("\nModel Accuracy:", round(accuracy_score(y_test, y_pred)*100,2), "%")
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))

# ------------------------------------------------
# 4️⃣ FUNCTION: CITY → LAT LONG
# ------------------------------------------------

def get_lat_long(city_name):
    geolocator = Nominatim(user_agent="flood_prediction_app")
    location = geolocator.geocode(city_name)
    if location:
        return (location.latitude, location.longitude)
    else:
        return None

# ------------------------------------------------
# 5️⃣ FIND NEAREST LOCATION IN DATASET
# ------------------------------------------------

def find_nearest_location(city_coords):
    min_distance = float("inf")
    nearest_row = None
    
    for index, row in df.iterrows():
        dataset_coords = (row["Latitude"], row["Longitude"])
        distance = geodesic(city_coords, dataset_coords).km
        
        if distance < min_distance:
            min_distance = distance
            nearest_row = row
    
    return nearest_row

# ------------------------------------------------
# 6️⃣ CITY BASED PREDICTION
# ------------------------------------------------

def predict_by_city(city_name):
    coords = get_lat_long(city_name)
    
    if coords is None:
        print("City not found!")
        return
    
    nearest = find_nearest_location(coords)
    
    if nearest is None:
        print("No matching location found!")
        return
    
    sample = nearest.drop(labels=["Flood Occurred"]).values.reshape(1, -1)
    sample = imputer.transform(sample)
    
    prediction = model.predict(sample)[0]
    probability = model.predict_proba(sample)[0][1]
    
    print("\nCity:", city_name)
    print("Nearest Dataset Location:",
          nearest["Latitude"], nearest["Longitude"])
    print("Flood Prediction:", "YES" if prediction == 1 else "NO")
    print("Flood Probability:", round(probability*100,2), "%")

# ------------------------------------------------
# 7️⃣ USER INPUT
# ------------------------------------------------

city_input = input("\nEnter City Name: ")
predict_by_city(city_input)