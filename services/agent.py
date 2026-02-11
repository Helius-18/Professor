"""Agno Agent with dynamic tools loaded from database.

Uses ToolBuilder to load Connection and Tool records from the DB and
creates agno-compatible tools for the Agent.
"""
from typing import List

from agno.agent import Agent, RunOutput
from agno.models.google import Gemini
from agno.models.openai import OpenAIChat
from agno.utils.pprint import pprint_run_response
from dotenv import load_dotenv

# Ensure project root is on sys.path so `python services\agent.py` works
from pathlib import Path
import sys

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.tool_builder import create_tools_for_agent

load_dotenv()  # Load environment variables from .env file


def create_agent_with_dynamic_tools() -> Agent:
    """Create an agno Agent with dynamically loaded tools from the database.

    Returns:
        Agent configured with tools from the connections and tools tables.
    """
    # Load tools from database
    dynamic_tools: List = create_tools_for_agent()

    agent = Agent(
        model=OpenAIChat(),
        tools=dynamic_tools,
        instructions="Use available tools to accomplish tasks. Be thorough and accurate.",
        markdown=True,
    )

    return agent


if __name__ == "__main__":
    # Example usage: create agent and run a prompt
    agent = create_agent_with_dynamic_tools()

    # Run agent and return the response as a variable
    response: RunOutput = agent.run("Retrieve all the ML pipelines")

    # Print the response in markdown format
    pprint_run_response(response, markdown=True)