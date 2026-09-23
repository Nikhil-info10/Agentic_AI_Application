# This is the app's user interface.
# It displays a chat box and a sidebar with the current support tickets.
# The user types a question, the AI answers, and the app may also run tools behind the scenes.

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agent import graph
from tools import get_all_tickets

# Set the page title and layout.
st.set_page_config(page_title="IT Support Agent AI", page_icon="🤖", layout="wide")

# Show the app title at the top of the page.
st.title("🤖 Enterprise IT Support Assistant")
st.caption("Powered by LangGraph Agentic Framework with Custom State Routing & SQLite Backend")

# Keep chat history in memory while the user uses the app.
# If no chat history exists yet, create an empty list.
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------------------
# Sidebar: shows live IT support tickets stored in SQLite.
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("🏢 Live Ticket Database")
    st.caption("Real-time view of SQLite state rows")

    # Load all tickets from the database.
    tickets = get_all_tickets()

    # If there are no tickets, show a friendly message.
    if not tickets:
        st.info("No tickets recorded in system.")
    else:
        # Show each ticket in the sidebar.
        for t in tickets:
            # Use green for open items and yellow for others.
            status_color = "🟢" if t["status"] == "Open" else "🟡"
            with st.container(border=True):
                st.markdown(f"**ID:** {t['ticket_id']} {status_color} `{t['status']}`")
                st.markdown(f"**Employee:** {t['employee_id']}")
                st.text_area("Issue Description", value=t['issue'], height=60, disabled=True, key=f"side_{t['ticket_id']}")

    st.markdown("---")
    st.header("Admin Controls")

    # Button to clear the chat history.
    if st.button("Reset Chat Session", type="primary"):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------------------------
# Display the past chat history in the main area.
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage) and msg.content:
        with st.chat_message("assistant"):
            st.write(msg.content)
    elif isinstance(msg, ToolMessage):
        with st.expander(f"🛠️ Executed Tool Call: {msg.name}", expanded=False):
            st.code(msg.content, language="json")

# ---------------------------------------------------------------------------
# Main chat box: wait for new user input.
# ---------------------------------------------------------------------------
if prompt := st.chat_input("How can I assist you with IT support today?"):
    # Show the user's question in the chat.
    with st.chat_message("user"):
        st.write(prompt)

    # Save the user message to the chat history.
    st.session_state.messages.append(HumanMessage(content=prompt))

    # Let the AI respond and run any needed tools.
    with st.chat_message("assistant"):
        response_placeholder = st.empty()

        inputs = {"messages": st.session_state.messages}
        events = graph.stream(inputs, stream_mode="values")

        final_state = None
        for event in events:
            final_state = event

            # If the AI used a tool, show the tool result in a section.
            for msg in event.get("messages", []):
                if isinstance(msg, ToolMessage) and msg not in st.session_state.messages:
                    with st.expander(f"🛠️ Tool Running: {msg.name}", expanded=True):
                        st.code(msg.content)

        if final_state:
            # Save the updated conversation state.
            st.session_state.messages = final_state["messages"]
            final_ai_reply = st.session_state.messages[-1].content
            response_placeholder.write(final_ai_reply)

            # Refresh the page so the sidebar ticket list shows latest data.
            st.rerun()
