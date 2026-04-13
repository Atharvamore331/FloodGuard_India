import os
import requests

DEFAULT_OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather_by_city(city_name):
    api_key = os.getenv("OPENWEATHER_API_KEY", DEFAULT_OPENWEATHER_API_KEY)
    if not api_key:
        return {"summary": "Weather unavailable (OPENWEATHER_API_KEY not set)"}

    try:
        params = {"q": city_name, "appid": api_key, "units": "metric"}
        response = requests.get(OPENWEATHER_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        pressure = data["main"].get("pressure")
        rain_1h = data.get("rain", {}).get("1h", 0.0)
        rain_3h = data.get("rain", {}).get("3h", 0.0)

        return {
            "summary": f"{desc}, {temp} C, humidity {humidity}%",
            "temperature": temp,
            "humidity": humidity,
            "pressure": pressure,
            "rain_1h": rain_1h,
            "rain_3h": rain_3h,
        }
    except Exception as exc:
        return {"summary": f"Weather unavailable ({exc})"}
