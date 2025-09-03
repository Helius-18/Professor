import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from agent import stream_graph
import uuid

st.set_page_config(page_title="Assistant", page_icon="🤖")

# Hidden thread id (do not expose UI for thread management)
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# session messages
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Assistant")
st.caption("Ask anything")

# render existing messages using Streamlit's chat components
for msg in st.session_state.messages:
    # only show user and assistant (AI) messages; ignore tool outputs
    if isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)
    elif isinstance(msg, AIMessage):
        st.chat_message("assistant").write(msg.content)

# collect user input using chat_input (falls back to text_input if not available)
if hasattr(st, "chat_input"):
    user_input = st.chat_input(placeholder="Ask anything")
else:
    user_input = st.text_input("", placeholder="Ask anything")

if user_input:
    # append user message and render it
    user_msg = HumanMessage(content=user_input)
    st.session_state.messages.append(user_msg)
    st.chat_message("user").write(user_input)

    # Stream assistant response into a live assistant message
    assistant_placeholder = st.chat_message("assistant")
    buffer = ""
    try:
        # iterate stream chunks, but only display assistant (AIMessage) content
        for chunk in stream_graph(st.session_state.messages, thread_id=st.session_state.thread_id):
            msgs = chunk.get("messages", [])
            # find last AIMessage in the chunk
            last_ai = None
            for m in reversed(msgs):
                if isinstance(m, AIMessage):
                    last_ai = m
                    break
            if last_ai is None:
                # nothing to display this iteration
                continue
            content = last_ai.content if hasattr(last_ai, "content") else str(last_ai)
            buffer = content
            assistant_placeholder.write(buffer)
        # final append only if we have AI content and it's not a duplicate of the last stored AI message
        if buffer:
            last_stored = None
            if st.session_state.messages:
                last_stored = st.session_state.messages[-1]
            if not (isinstance(last_stored, AIMessage) and getattr(last_stored, "content", "").strip() == buffer.strip()):
                st.session_state.messages.append(AIMessage(content=buffer))
    except Exception as e:
        st.error(f"Assistant error: {e}")