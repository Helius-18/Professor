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
                # Use invoke instead of stream for better compatibility
                response = agent.invoke({"input": prompt})
                full_response = response.get("output", str(response))
                placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"Error: {str(e)}"
                placeholder.markdown(full_response)

    st.session_state.history.append(("assistant", full_response))
