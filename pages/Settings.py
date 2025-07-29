import streamlit as st
import shutil

st.set_page_config(page_title="Settings", layout="centered")

st.title("⚙️ Settings")

# ---- MCP Servers ----
st.subheader("Available MCP Servers")

mcp_candidates = ["mcp-weather", "mcp-code", "mcp-db", "mcp-llm"]
available_mcps = [name for name in mcp_candidates if shutil.which(name)]

if available_mcps:
    for mcp in available_mcps:
        st.write(f"✅ {mcp}")
else:
    st.warning("No MCP servers found on this system.")
