from langgraph.prebuilt import create_react_agent
from models.openai_model import get_openai_llm
from tools.weather_tool import weather_tool

def get_openai_agent():
    llm = get_openai_llm()
    tools = [weather_tool]

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt="You are a helpful assistant.",
        verbose=True,
        handle_errors=True
    )
    return agent
