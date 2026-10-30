"""Streamlit Web Chat Interface for DevMate.

Provides an interactive dashboard and chat experience with:
- Conversational state management
- Interactive visual cards for Jira tickets and GitHub PRs
- Human-in-the-Loop confirmation triggers for state mutations
- Settings sidebar for toggling Live API vs Mock Mode
"""

import streamlit as st
from typing import Dict, Any, List
import os

from app.config import settings
from app.agent import agent
from app.tools.jira_tool import jira_tool
from app.tools.github_tool import github_tool

# Set page configuration
st.set_page_config(
    page_title="DevMate - AI DevOps Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling cards and badges
st.markdown("""
<style>
    .stChatMessage {
        padding: 0.75rem 1rem;
        border-radius: 0.75rem;
    }
    .badge-high {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 0.2rem 0.5rem;
        border-radius: 0.375rem;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-medium {
        background-color: #fef3c7;
        color: #92400e;
        padding: 0.2rem 0.5rem;
        border-radius: 0.375rem;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-status {
        background-color: #e0e7ff;
        color: #3730a3;
        padding: 0.2rem 0.5rem;
        border-radius: 0.375rem;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .card-box {
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 0.85rem;
        margin-bottom: 0.5rem;
        background-color: #f9fafb;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state for chat and actions
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Welcome to DevMate!** I am your DevOps & Engineering Assistant.\n\n"
                "I can help automate your workflow across **Jira** and **GitHub**:\n"
                "- 📋 *'List my assigned tickets'* or *'Show stories in progress'*\n"
                "- ➕ *'Create a bug for database timeout on login'*\n"
                "- 🔄 *'Move DEV-102 to Done'*\n"
                "- 🐙 *'Show open pull requests'* or *'Approve PR #42'*"
            ),
            "tool_type": "welcome",
            "tool_result": None
        }
    ]

if "pending_confirmation" not in st.session_state:
    st.session_state.pending_confirmation = None


# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.title("⚙️ DevMate Settings")
    st.caption("AI-Powered Platform Engineering Assistant")

    st.divider()

    # Mode Selector
    mock_active = st.toggle("🧪 Enable Mock Mode", value=settings.MOCK_MODE, help="Use offline in-memory data for safe testing and demos")
    if mock_active != settings.MOCK_MODE:
        settings.MOCK_MODE = mock_active
        jira_tool.mock_mode = mock_active
        github_tool.mock_mode = mock_active
        st.toast(f"Switched to {'Mock Mode' if mock_active else 'Live API Mode'}!")

    if settings.MOCK_MODE:
        st.success("🟢 Running in Mock Mode (Zero-cost, offline ready)")
    else:
        st.info("🌐 Running with Live APIs")

    st.divider()
    st.subheader("🔑 Credentials & Tokens")
    with st.expander("Configure API Keys"):
        gemini_key = st.text_input("Gemini API Key", value=settings.GEMINI_API_KEY or "", type="password")
        gh_token = st.text_input("GitHub Token", value=settings.GITHUB_TOKEN or "", type="password")
        jira_token = st.text_input("Jira API Token", value=settings.JIRA_API_TOKEN or "", type="password")
        
        if st.button("Apply Credentials"):
            if gemini_key:
                settings.GEMINI_API_KEY = gemini_key
                agent._init_llm()
            if gh_token:
                settings.GITHUB_TOKEN = gh_token
                github_tool.mock_mode = False
            if jira_token:
                settings.JIRA_API_TOKEN = jira_token
                jira_tool.mock_mode = False
            st.success("Credentials updated!")

    st.divider()
    st.markdown("### 💡 Quick Prompt Suggestions")
    if st.button("📋 List My Jira Tickets"):
        st.session_state.user_prompt_inject = "List my assigned tickets on Jira"
    if st.button("🔍 Show Open PRs"):
        st.session_state.user_prompt_inject = "Show open pull requests on git"
    if st.button("✅ Approve PR #42"):
        st.session_state.user_prompt_inject = "Approve PR #42"

    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.pending_confirmation = None
        st.rerun()


# --- MAIN CHAT DISPLAY ---
st.title("🤖 DevMate: Engineering Copilot")
st.caption("Connected to Jira Cloud & GitHub Repositories")


def render_tool_output(tool_type: str, tool_result: Any):
    """Renders formatted cards and data widgets for different tool responses."""
    if not tool_result:
        return

    # Render Jira tickets list
    if tool_type == "jira_list" and isinstance(tool_result, list):
        for issue in tool_result:
            priority_class = "badge-high" if issue.get("priority") == "High" else "badge-medium"
            st.markdown(f"""
            <div class="card-box">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>🎫 {issue.get('key')} - {issue.get('summary')}</strong>
                    <div>
                        <span class="badge-status">{issue.get('status')}</span>
                        <span class="{priority_class}">{issue.get('priority')}</span>
                    </div>
                </div>
                <div style="font-size: 0.85rem; color: #4b5563; margin-top: 0.4rem;">
                    Type: <b>{issue.get('issue_type')}</b> | Assignee: <b>{issue.get('assignee')}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Render GitHub Pull Requests list
    elif tool_type == "github_prs" and isinstance(tool_result, list):
        for pr in tool_result:
            st.markdown(f"""
            <div class="card-box">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>🐙 PR #{pr.get('number')}: {pr.get('title')}</strong>
                    <span class="badge-status">{pr.get('state', 'open').upper()}</span>
                </div>
                <div style="font-size: 0.85rem; color: #4b5563; margin-top: 0.4rem;">
                    Author: <b>@{pr.get('author')}</b> | Created: <b>{pr.get('created_at')}</b> | <a href="{pr.get('html_url')}" target="_blank">View on GitHub ↗</a>
                </div>
            </div>
            """, unsafe_allow_html=True)


# Render conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_result"):
            render_tool_output(msg.get("tool_type"), msg.get("tool_result"))


# --- HUMAN-IN-THE-LOOP CONFIRMATION DIALOG ---
if st.session_state.pending_confirmation:
    pending = st.session_state.pending_confirmation
    st.warning("⚠️ **Action Required: Confirmation Guardrail**")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("✅ Confirm & Execute", type="primary", use_container_width=True):
            with st.spinner("Executing confirmed action..."):
                result = agent.process_query("Confirm", confirmation_payload=pending)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["response"],
                    "tool_type": result.get("tool_type"),
                    "tool_result": result.get("tool_result")
                })
                st.session_state.pending_confirmation = None
                st.rerun()

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Action cancelled by user.",
                "tool_type": "cancelled",
                "tool_result": None
            })
            st.session_state.pending_confirmation = None
            st.rerun()


# --- CHAT INPUT HANDLING ---
# Check if a prompt was injected via quick suggestion buttons
user_input = None
if "user_prompt_inject" in st.session_state and st.session_state.user_prompt_inject:
    user_input = st.session_state.user_prompt_inject
    st.session_state.user_prompt_inject = None
else:
    user_input = st.chat_input("Ask DevMate (e.g., 'List assigned Jira tickets', 'Approve PR #42')...")

if user_input:
    # Append user prompt to UI
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process query through DevMate AI Agent
    with st.chat_message("assistant"):
        with st.spinner("DevMate is analyzing and communicating with tools..."):
            agent_result = agent.process_query(user_input)

            st.markdown(agent_result["response"])
            if agent_result.get("tool_result"):
                render_tool_output(agent_result.get("tool_type"), agent_result.get("tool_result"))

            # Store in session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": agent_result["response"],
                "tool_type": agent_result.get("tool_type"),
                "tool_result": agent_result.get("tool_result")
            })

            # Check if this requires human confirmation
            if agent_result.get("requires_confirmation"):
                st.session_state.pending_confirmation = agent_result.get("pending_action")
                st.rerun()
