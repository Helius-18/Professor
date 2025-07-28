from langchain_core.tools import Tool
from models.llama_model import get_llm

llm = get_llm()

def general_qa(question: str) -> str:
    prompt = f"You are a helpful assistant. Answer the user's question directly:\n\nUser: {question}"
    return llm.invoke(prompt)

general_tool = Tool(
    name="GeneralQA",
    func=general_qa,
    description="Use for general questions not related to weather."
)
