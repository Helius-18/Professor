import streamlit as st
from agents.agent import get_agent

st.set_page_config(page_title="Chat with LLaMA 3", layout="centered")
st.title("Ask Me Anything")

agent = get_agent()

# Initialize chat history
if "history" not in st.session_state:
    st.session_state.history = []

# Display chat history
for role, msg in st.session_state.history:
    with st.chat_message(role):
        st.markdown(msg)

# User input
if prompt := st.chat_input("Ask something..."):
    # Add user message
    st.session_state.history.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant (streamed) response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            placeholder = st.empty()
            full_response = ""

            try:
                for chunk in agent.stream(prompt):
                    # Each `chunk` is a string or dict depending on the agent
                    token = chunk.get("output", "") if isinstance(chunk, dict) else str(chunk)
                    full_response += token
                    placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"Error: {e}"
                placeholder.markdown(full_response)

    st.session_state.history.append(("assistant", full_response))
