from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
import os
import json
import numpy as np
import faiss


def document_processor(state: MessagesState):
    """Get information about everything and every question like what?, how?, who?, where?, etc.
    This is a tiny example tool that the graph can call.
    """
    last = state["messages"][-1].content if state["messages"] else ""
    print(f"Document processor received message: {last}")

    # Load FAISS index and metadata (we expect files in ChatBot/documents/context.faiss and .meta.jsonl)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    docs_dir = os.path.join(base_dir, "documents")
    base_name = "context"
    faiss_path = os.path.join(docs_dir, f"{base_name}.faiss")
    meta_path = os.path.join(docs_dir, f"{base_name}.meta.jsonl")

    try:
        # load metadata
        metas = []
        with open(meta_path, "r", encoding="utf-8") as mf:
            for line in mf:
                try:
                    metas.append(json.loads(line))
                except Exception:
                    metas.append({"text": line.strip()})

        # load index
        index = faiss.read_index(faiss_path)

        # embed query
        embedder = OpenAIEmbeddings(api_key="api-key")
        try:
            qvec = embedder.embed_query(last)
        except Exception:
            qvec = embedder.embed_documents([last])[0]

        qnp = np.array(qvec, dtype=np.float32)
        # normalize (index was built with normalized vectors)
        norm = np.linalg.norm(qnp)
        if norm == 0:
            norm = 1.0
        qnp = (qnp / norm).reshape(1, -1)

        k = 3
        D, I = index.search(qnp, k)
        hits = []
        for idx in I[0]:
            if idx < 0 or idx >= len(metas):
                continue
            hits.append(metas[idx].get("text") if isinstance(metas[idx], dict) else str(metas[idx]))

        if not hits:
            return "Please let the user know that You dont have the information to answer that question."

        context = "\n\n---\n\n".join(hits)

        return context + ".\n Here is the information, Please reponsd to the question based on this information."
    
    except Exception as e:

        return "Please let the user know that You are not able to answer that question."


tools = [document_processor]

# Create an LLM instance; prefer environment-based API keys instead of hard-coding them here.
llm = ChatOpenAI(model="gpt-4o", api_key="api-key")
llm_with_tools = llm.bind_tools(tools)

sys_msg = SystemMessage(content=(
    "You are a helpful assistant. Always use the available tools to retrieve information, even if you know the answer."
))


def assistant(state: MessagesState):
    # The assistant node invokes the LLM (with tools) and returns the assistant message
    msg = llm_with_tools.invoke([sys_msg] + state["messages"])

    # post-process to remove accidental echo of the last human message
    try:
        last_human = None
        for m in reversed(state["messages"]):
            if isinstance(m, HumanMessage):
                last_human = m
                break

        if last_human and hasattr(msg, "content") and msg.content:
            text = msg.content
            prefix = last_human.content.strip()
            if prefix and text.startswith(prefix):
                # remove the prefix and any leading separators
                new_text = text[len(prefix):].lstrip("\n\r :-–—")
                # update message content if it changed
                if new_text:
                    # preserve the message type if possible
                    try:
                        msg.content = new_text
                    except Exception:
                        text = new_text
    except Exception:
        # be conservative — if anything goes wrong, just return the original msg
        pass

    return {"messages": [msg]}


def build_react_graph():
    """Build and compile the StateGraph with a checkpointer and store.

    If a sqlite path is provided and SqliteSaver is available, it will be used so thread
    checkpoints survive process restarts. Otherwise an in-memory MemorySaver is used.
    """
    memory = MemorySaver()
    
    builder = StateGraph(MessagesState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")
    builder.add_edge("assistant", END)

    compiled = builder.compile(checkpointer=memory)
    return compiled


def stream_graph(messages, thread_id: str | None = None, stream_mode: str = "values"):
    """Stream the graph execution. Yields chunks returned by LangGraph's stream API.

    Each yielded chunk is a dict similar to the non-streaming return; typically the
    assistant message at chunk['messages'][-1] will be updated incrementally.
    """
    graph = build_react_graph()
    config = {"configurable": {}}
    if thread_id:
        config["configurable"]["thread_id"] = str(thread_id)

    for chunk in graph.stream({"messages": messages}, config, stream_mode=stream_mode):
        yield chunk