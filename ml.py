import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from weather import get_weather_by_city


df = pd.read_csv("India_Flood_Dataset.csv")
print("Dataset Loaded Successfully")
print("Total Rows:", len(df))

df = pd.get_dummies(df, columns=["State"], drop_first=True)

X_df = df.drop("Flood_Occurred", axis=1)
y = df["Flood_Occurred"]

imputer = SimpleImputer(strategy="median")
scaler = StandardScaler()

X_imputed = imputer.fit_transform(X_df)
X_scaled = scaler.fit_transform(X_imputed)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

model = XGBClassifier(
    n_estimators=600,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    gamma=0.1,
    reg_alpha=0.5,
    reg_lambda=1,
    scale_pos_weight=1,
    random_state=42,
    eval_metric="logloss",
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print("\n==============================")
print("MODEL PERFORMANCE")
print("==============================")
print("Accuracy:", round(accuracy * 100, 2), "%")
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))
print("\nConfusion Matrix:\n")
print(confusion_matrix(y_test, y_pred))

cv_scores = cross_val_score(model, X_scaled, y, cv=5)
print("\nCross Validation Accuracy:", round(cv_scores.mean() * 100, 2), "%")

feature_defaults = X_df.median(numeric_only=True).to_dict()
feature_columns = X_df.columns.tolist()

CITY_STATE_MAP = {
    "mumbai": "Maharashtra",
    "pune": "Maharashtra",
    "nagpur": "Maharashtra",
    "nashik": "Maharashtra",
    "thane": "Maharashtra",
    "kolkata": "West Bengal",
    "siliguri": "West Bengal",
    "bengaluru": "Karnataka",
    "bangalore": "Karnataka",
    "chennai": "Tamil Nadu",
    "coimbatore": "Tamil Nadu",
    "hyderabad": "Telangana",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "ahmedabad": "Gujarat",
    "surat": "Gujarat",
    "jaipur": "Rajasthan",
    "lucknow": "Uttar Pradesh",
    "kanpur": "Uttar Pradesh",
    "patna": "Bihar",
    "kochi": "Kerala",
    "thiruvananthapuram": "Kerala",
    "guwahati": "Assam",
    "bhubaneswar": "Odisha",
}


def map_weather_to_rainfall_mm(weather):
    rain_1h = float(weather.get("rain_1h", 0.0))
    rain_3h = float(weather.get("rain_3h", 0.0))
    hourly_mm = max(rain_1h, rain_3h / 3.0)
    # Simple conversion for model input scale; replace with better temporal features if available.
    return hourly_mm * 24.0 * 30.0


def build_city_sample(city_name, weather):
    sample = feature_defaults.copy()

    sample["Monthly_Rainfall_mm"] = map_weather_to_rainfall_mm(weather)

    if "humidity" in weather:
        sample["Soil_Moisture_%"] = float(weather["humidity"])
        sample["Reservoir_Level_%"] = float(weather["humidity"])

    rainfall_mm = float(sample.get("Monthly_Rainfall_mm", 0.0))
    sample["Previous_Month_Rainfall"] = max(0.0, rainfall_mm * 0.7)
    sample["River_Discharge_Cumecs"] = max(
        0.0, rainfall_mm * 2.5 * (feature_defaults["River_Discharge_Cumecs"] / 200.0)
    )

    city_key = city_name.strip().lower()
    mapped_state = CITY_STATE_MAP.get(city_key)
    if mapped_state:
        col_name = f"State_{mapped_state}"
        if col_name in feature_columns:
            for col in feature_columns:
                if col.startswith("State_"):
                    sample[col] = 0.0
            sample[col_name] = 1.0

    sample_df = pd.DataFrame([sample], columns=feature_columns)
    sample_imputed = imputer.transform(sample_df)
    sample_scaled = scaler.transform(sample_imputed)
    return sample_scaled


def predict_city_flood_risk(city_name):
    weather = get_weather_by_city(city_name)
    if weather.get("summary", "").startswith("Weather unavailable"):
        print("\nWeather API error:", weather["summary"])
        return None

    sample = build_city_sample(city_name, weather)
    probability = float(model.predict_proba(sample)[0][1])
    prediction = int(probability >= 0.5)

    if probability >= 0.8:
        risk = "CRITICAL FLOOD RISK"
    elif probability >= 0.6:
        risk = "HIGH FLOOD RISK"
    elif probability >= 0.4:
        risk = "MODERATE FLOOD RISK"
    else:
        risk = "LOW FLOOD RISK"

    print("\n--------------------------------")
    print("City:", city_name)
    print("Weather:", weather["summary"])
    print("Flood Risk:", risk)
    print("Flood Probability:", round(probability * 100, 2), "%")
    print("Predicted Label:", prediction)
    print("--------------------------------")
    return probability


if __name__ == "__main__":
    print("\nModel ready for realtime city prediction.")
    city = input("Enter city name: ").strip()
    if city:
        predict_city_flood_risk(city)
    else:
        print("No city entered.")
