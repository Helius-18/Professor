# Professor: LangChain MCP + LLM Chatbot with OLLAMA UI

A chatbot application that uses [LangChain](https://python.langchain.com/), OLLAMA LLMs (like Llama 3), and Streamlit to provide a chat interface with tool-augmented reasoning (MCP). Includes weather and general Q&A tools.

## Features

- Chat UI built with Streamlit
- Integrates OLLAMA LLMs (Llama 3 by default)
- Weather tool (fetches live weather using wttr.in, no API key needed)
- General Q&A tool (for non-weather questions)
- Easily extensible with more tools

## Project Structure

```
main.py                # Streamlit UI
professor.py           # Standalone CLI agent example
agents/
    agent.py           # Agent setup with tools
models/
    llama_model.py     # LLM model loader
tools/
    general_tool.py    # General Q&A tool
    weather_tool.py    # Weather info tool
requirements.txt       # Python dependencies
```

## Setup

1. **Install OLLAMA and pull a model (e.g., Llama 3):**
   ```
   ollama pull llama3
   ollama serve
   ```

2. **Install Python dependencies:**
   ```
   pip install -r requirements.txt
   ```

3. **Run the Streamlit UI:**
   ```
   streamlit run main.py
   ```

4. **(Optional) Run the CLI agent:**
   ```
   python professor.py
   ```

## Usage

- Open the Streamlit app in your browser.
- Ask questions like:
  - "What's the weather in Paris?"
  - "Who is Albert Einstein?"
- The agent will use the appropriate tool (weather or general Q&A) and respond.

## Requirements

- Python 3.8+
- OLLAMA running locally with a supported LLM (e.g., llama3)
- See `requirements.txt` for Python packages

## Extending

- Add new tools in the `tools/` directory and register them in `agents/agent.py`.