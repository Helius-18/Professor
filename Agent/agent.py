# agent.py
from __future__ import annotations

from typing import Any, Dict, List

from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, START, StateGraph
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage

from dynamic_tools import load_dynamic_tools  # <-- new helper


# 1. Load tools from DB
tools = load_dynamic_tools("sqlite:///app.db")

# 2. Set up LLM with tools
llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
llm_with_tools = llm.bind_tools(tools)

# 3. Memory / state
memory = MemorySaver()


# 4. Assistant node: calls the LLM
def assistant(state: MessagesState):
    """
    LangGraph node: takes state["messages"], calls LLM with tools, returns new message.
    """
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# 5. Build the graph
builder = StateGraph(MessagesState)

builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

react_graph = builder.compile(checkpointer=memory)


def chat_loop():
    """
    Simple CLI loop to talk to the agent.
    """
    # new conversation thread
    config = {"configurable": {"thread_id": "thread-1"}}

    # System message to guide behavior
    messages: List[Any] = [
        SystemMessage(
            content=(
                "You are a helpful assistant with access to dynamic DB/API tools. "
                "Use tools whenever needed to answer factual/data questions. "
                "Explain results clearly."
            )
        )
    ]

    print("Dynamic LangGraph Agent (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        messages.append(HumanMessage(content=user_input))

        # Run the graph
        state = react_graph.invoke({"messages": messages}, config)

        # Update messages from state (so tool calls are preserved)
        messages = state["messages"]

        # Last message is model's reply
        last = messages[-1]
        print(f"Agent: {last.content}")


if __name__ == "__main__":
    chat_loop()
