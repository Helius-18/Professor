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

    # Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            placeholder = st.empty()
            full_response = ""
            try:
                # Use invoke instead of run (no streaming)
                response = agent.invoke({
                    "input": prompt,
                    "chat_history": st.session_state.history
                })
                # If response is a dict with 'output', extract it
                if isinstance(response, dict) and "output" in response:
                    full_response = response["output"]
                else:
                    full_response = str(response)
                placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"Error: {e}"
                placeholder.markdown(full_response)

    st.session_state.history.append(("assistant", full_response))
