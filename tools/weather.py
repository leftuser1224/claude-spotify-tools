"""Weather tools for getting current weather data"""

import json
import urllib.request
import urllib.error


async def get_weather(location: str) -> dict:
    """Get current weather information for a location from wttr.in API

    Args:
        location: City name (e.g., 'Tokyo', 'New York', '東京')

    Returns:
        Dictionary with weather, temperature, and local time information
    """
    try:
        location_encoded = location.replace(" ", "+")
        url = f"https://wttr.in/{location_encoded}?format=j1"

        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())

        current = data.get("current_condition", [{}])[0]

        weather_desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
        temp_c = current.get("temp_C")

        # Try to get local time
        local_time = current.get("localObsDateTime", "")
        if not local_time:
            local_time = current.get("observation_time", "Unknown")

        return {
            "location": location,
            "weather": weather_desc,
            "temp_c": temp_c,
            "local_time": local_time,
            "success": True
        }
    except Exception as e:
        return {
            "location": location,
            "success": False,
            "error": str(e)
        }
