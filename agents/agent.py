from tools.weather_tool import weather_tool
from models.llama_model import get_llm
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType

def get_agent():
    llm = get_llm()
    tools = [weather_tool]
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
    )
    return agent
