# This file defines the AI assistant brain.
# It connects the user chat to OpenAI and to the helper tools that search the knowledge base,
# look up tickets, and create new support tickets.

import os
from typing import Annotated, TypedDict
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# Import the custom helper functions from the tools file.
# These are the actions the AI can choose to do during a conversation.
from tools import search_knowledge_base, lookup_ticket, create_ticket

# ---------------------------------------------------------------------------
# Tool 1: search the IT knowledge base
# ---------------------------------------------------------------------------
@tool
def kb_tool(query: str):
    """Searches the IT knowledge base for helpful solutions to technical problems."""
    # This is a simple wrapper around the database search logic.
    return search_knowledge_base(query)

# ---------------------------------------------------------------------------
# Tool 2: look up ticket history by employee ID
# ---------------------------------------------------------------------------
@tool
def lookup_tool(employee_id: str):
    """Looks up existing IT support ticket history for a user using their Employee ID."""
    # This lets the assistant check whether the user already has a ticket.
    return lookup_ticket(employee_id)

# ---------------------------------------------------------------------------
# Tool 3: create a ticket if the user asks for it
# ---------------------------------------------------------------------------
@tool
def create_tool(employee_id: str, issue: str):
    """Creates a new IT support ticket when explicitly requested by a user."""
    # This is only used when the user asks to open a support case.
    return create_ticket(employee_id, issue)

# All available tools for the AI assistant.
# The AI can choose one or more of these based on the user request.
tools = [kb_tool, lookup_tool, create_tool]

# ToolNode is the part of LangGraph that runs the chosen tool(s).
tool_node = ToolNode(tools)

# This defines the structure of the conversation state.
# A state is the memory of the chat: messages sent so far.
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Create the OpenAI chat model.
# "bind_tools" tells the model it is allowed to use our custom tools.
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)

# ---------------------------------------------------------------------------
# The AI decides what to say and do for each user message.
# ---------------------------------------------------------------------------
def call_model(state: AgentState):
    # System message = instructions for the AI.
    # It tells the AI how to behave and what safety rules to follow.
    system_prompt = SystemMessage(content=(
        "You are an expert IT Support Assistant for a corporate environment.\n"
        "Your goals are to troubleshoot via knowledge bases, look up ticket states, or create tickets.\n"
        "CRITICAL SAFETY RULES:\n"
        "1. BEFORE creating a ticket or looking up historical records, you MUST verify and collect the user's Employee ID.\n"
        "2. If the user asks you to create a ticket but hasn't given an Employee ID, explicitly ask for it first.\n"
        "3. Do not make up fake ticket IDs. Rely only on tool outputs.\n"
        "4. Be friendly, structured, and distinct about what is data vs. your diagnostic recommendation."
    ))

    # Combine system instructions with the actual conversation history.
    messages = [system_prompt] + state["messages"]

    # Ask the LLM to respond based on the conversation.
    response = llm.invoke(messages)

    # Return the AI's reply so it can be added to the chat state.
    return {"messages": [response]}

# ---------------------------------------------------------------------------
# Decide whether the AI should use a tool or finish the response.
# ---------------------------------------------------------------------------
def should_continue(state: AgentState):
    # Look at the newest message from the AI.
    last_message = state["messages"][-1]

    # If the AI decided to call a tool, route to the tools node.
    if last_message.tool_calls:
        return "tools"

    # If no tools are needed, end the workflow.
    return END

# ---------------------------------------------------------------------------
# Build the workflow / decision tree.
# This is the step-by-step flow the AI follows.
# ---------------------------------------------------------------------------
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

# Final compiled workflow that can be used by the app.
graph = workflow.compile()
