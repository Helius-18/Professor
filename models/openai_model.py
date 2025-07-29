from langchain_openai import ChatOpenAI

def get_openai_llm(model_name="gpt-3.5-turbo"):
    openai_api_key = 'api_key'
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")
    return ChatOpenAI(openai_api_key=openai_api_key, model_name=model_name, streaming=True)
