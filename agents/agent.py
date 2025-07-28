from langchain.agents import initialize_agent, AgentType
from tools.weather_tool import weather_tool
from tools.general_tool import general_tool
from models.llama_model import get_llm

def get_agent():
    llm = get_llm()
    # tools = [weather_tool, general_tool]
    tools = [weather_tool]
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        stream_output=True
    )
    return agent
