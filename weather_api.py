import requests

import os
API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

city = input("Enter city name: ")
url = f"{BASE_URL}?q={city}&appid={API_KEY}&units=metric"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    if "main" in data:
        weather_data = {
            "city": city,
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "description": data["weather"][0]["description"]
        }
        print(weather_data)
    else:
        print("⚠️ 'main' field missing in response. Full data:", data)
else:
    print(f"❌ Failed to fetch data. Status Code: {response.status_code}")
    print("Response:", response.text)
