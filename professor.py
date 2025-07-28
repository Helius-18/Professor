import requests
from langchain_ollama.chat_models import ChatOllama
from langchain_core.tools import Tool
from langchain.agents import initialize_agent, AgentType

def get_weather(location: str) -> str:
    try:
        # wttr.in supports simple city queries and returns weather in plain text or JSON
        url = f"http://wttr.in/{location}?format=j1"
        response = requests.get(url)
        data = response.json()

        # Extract current weather info
        current = data["current_condition"][0]
        temp_c = current["temp_C"]
        weather_desc = current["weatherDesc"][0]["value"]
        feels_like = current["FeelsLikeC"]

        return (f"The current weather in {location.title()} is {weather_desc} "
                f"with a temperature of {temp_c}°C and feels like {feels_like}°C.")
    except Exception as e:
        return f"Failed to get weather data: {e}"

def general_question_answering(question: str) -> str:
    return llm.invoke(question)

weather_tool = Tool(
    name="WeatherInfo",
    func=get_weather,
    description="Get the current weather for a given city. Input should be a city name like 'Paris' or 'London'."
)

general_tool = Tool(
    name="GeneralQA",
    func=general_question_answering,
    description="Use this tool for general knowledge or questions not related to weather. Input is any question."
)


llm = ChatOllama(model="llama3:8b")


agent = initialize_agent(
    tools=[weather_tool, general_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True
)

user_question = input("Ask a question (e.g. 'What's the weather in London?'): ")
response = agent.run(user_question)
print("\n🧠 Agent Response:")
print(response)
