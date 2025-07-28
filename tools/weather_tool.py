import requests
from langchain_core.tools import Tool

def get_weather(location: str) -> str:
    try:
        url = f"http://wttr.in/{location}?format=j1"
        response = requests.get(url)
        data = response.json()
        current = data["current_condition"][0]
        temp_c = current["temp_C"]
        weather_desc = current["weatherDesc"][0]["value"]
        feels_like = current["FeelsLikeC"]
        return f"The current weather in {location.title()} is {weather_desc}, {temp_c}°C (feels like {feels_like}°C)."
    except Exception as e:
        return f"Failed to get weather data: {e}"

weather_tool = Tool(
    name="WeatherInfo",
    func=get_weather,
    description="Get the current weather for a city like 'Paris' or 'London'."
)
