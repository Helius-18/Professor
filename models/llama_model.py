from langchain_ollama.chat_models import ChatOllama

def get_llm():
    return ChatOllama(
        model="llama3:8b",
        temperature=0.1,  # Lower temperature for more consistent outputs
        num_predict=512,  # Limit response length
        system="""You are a helpful assistant that uses tools to answer questions.
            When you need to use a tool, respond with:
            Thought: [your reasoning]
            Action: [tool name]
            Action Input: [tool input]

            After receiving the tool output, provide a clear final answer.
            Do not use 'Action: None' - if you have the answer, just provide the Final Answer directly.
            Do not provide any suggestions to the user"""
    )
