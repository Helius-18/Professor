from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from tools.weather_tool import weather_tool
from tools.general_tool import general_tool
# from tools.dmg_tool import prevalidation_errors_tool, dq_errors_tool
from models.llama_model import get_llm

def get_agent():
    llm = get_llm()
    # tools = [weather_tool, general_tool]
    tools = [weather_tool]
    
    # Add memory to help with context
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,  # Better for conversational context
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=3,  # Limit iterations to prevent loops
        early_stopping_method="generate",  # Generate final answer if stuck
        memory=memory
    )
    return agent
