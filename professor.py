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
    name="Weather",
    func=get_weather,
    description="This Tool provides current weather information for a specified city. Input should be a city name like 'Paris' or 'London'."
)

# general_tool = Tool(
#     name="GeneralQuestionAnswering",
#     func=general_question_answering,
#     description="Use this tool for casual conversation or questions not related to weather. Input is any question."
# )


llm = ChatOllama(model="llama3:8b")


agent_executor = initialize_agent(
    tools=[weather_tool],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    #verbose=True,
    handle_parsing_errors=True

)

# print(agent_executor.agent.llm_chain.prompt.template)
user_question = input("Ask a question (e.g. 'What's the weather in London?'): ")
response = agent_executor.run({
    "input": user_question,
    "chat_history": []  # or your actual chat history if you have it
})
print("\n🧠 Agent Response:")
print(response)
