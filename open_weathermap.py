import requests

# Step 1: API key and base URL
API_KEY = "616bb6e88312cd11c5d068b6f126b54c"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# Step 2: Get city name
city = input("Enter city name: ")

# Step 3: Build request URL
url = f"{BASE_URL}?q={city}&appid={API_KEY}&units=metric"

# Step 4: Send GET request
response = requests.get(url)

# Step 5: Handle response
if response.status_code == 200:
    data = response.json()
    print(f"\nWeather in {city}: {data['weather'][0]['description']}")
    print(f"Temperature: {data['main']['temp']}°C")
    print(f"Humidity: {data['main']['humidity']}%")
else:
    print("❌ Error fetching weather data. Check city name or API key.")
