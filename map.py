import folium
from geopy.geocoders import Nominatim
import webbrowser
import os

# Initialize geocoder
geolocator = Nominatim(user_agent="flood_warning_system")

# User input
city = input("Enter city name: ")

# Get location
location = geolocator.geocode(city)

if location:
    lat, lon = location.latitude, location.longitude
    print(f"Opening map for {city} at ({lat}, {lon})")

    # Create map
    m = folium.Map(
        location=[lat, lon],
        zoom_start=11,
        tiles="OpenStreetMap"
    )

    # Marker
    folium.Marker(
        [lat, lon],
        popup=f"{city}",
        icon=folium.Icon(color="blue")
    ).add_to(m)

    # Save file
    file_name = f"{city.lower().replace(' ', '_')}_map.html"
    m.save(file_name)

    # Open in browser
    webbrowser.open('file://' + os.path.realpath(file_name))

else:
    print("City not found. Please enter a valid city.")