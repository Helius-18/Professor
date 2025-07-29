from langgraph.prebuilt import create_react_agent
from models.llama_model import get_llm
from tools.weather_tool import weather_tool
from tools.general_tool import general_tool

def get_agent():
    llm = get_llm()
    tools = [weather_tool]  # or [weather_tool, general_tool]
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt="You are a helpful assistant."
    )
    return agent
