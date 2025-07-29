import streamlit as st
from agents.openai_agent import get_openai_agent

st.set_page_config(page_title="Chat with LLaMA 3", layout="centered")
st.title("Ask Me Anything")

agent = get_openai_agent()

# Initialize chat history
if "history" not in st.session_state:
    st.session_state.history = []

# Display past chat history
for role, msg in st.session_state.history:
    with st.chat_message(role):
        st.markdown(msg)

# User input
if prompt := st.chat_input("Ask something..."):
    # Save user message
    st.session_state.history.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build messages list for agent
    messages = []
    for role, msg in st.session_state.history:
        messages.append({"role": role, "content": msg})

    # Assistant response (streamed)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        try:
            for message_chunk, metadata in agent.stream(
                {"messages": messages}, stream_mode="messages"
            ):
                print("DEBUG:", type(message_chunk), message_chunk)
                if hasattr(message_chunk, "content") and message_chunk.content:
                    if isinstance(message_chunk.content, str):
                        new_text = message_chunk.content[len(full_response):] if message_chunk.content.startswith(full_response) else message_chunk.content
                    elif isinstance(message_chunk.content, list):
                        combined = "".join([part["text"] for part in message_chunk.content if part.get("type") == "text"])
                        new_text = combined[len(full_response):] if combined.startswith(full_response) else combined
                    else:
                        new_text = ""

                    full_response += new_text
                    placeholder.markdown(full_response + "...")  # Add cursor effect
        except Exception as e:
            full_response = f"Error: {e}"
            placeholder.markdown(full_response)

        # Final clean text without cursor
        placeholder.markdown(full_response)

    # Save assistant response in history
    st.session_state.history.append(("assistant", full_response))
