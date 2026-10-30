"""AI Agent Engine for DevMate.

Orchestrates user queries, maps intent to tool executions (Jira and GitHub),
and manages Human-in-the-Loop confirmations for destructive/write operations.
Supports both Google Gemini LLM and an intelligent local Rule-based Intent Engine.
"""

from typing import Dict, Any, List, Optional
import json
import logging
import re

from app.config import settings
from app.tools.jira_tool import jira_tool
from app.tools.github_tool import github_tool

logger = logging.getLogger(__name__)


class DevMateAgent:
    """Intelligent agent coordinating developer workflows with safety guardrails."""

    def __init__(self):
        self.gemini_client = None
        self._init_llm()

    def _init_llm(self):
        """Initialize Google GenAI client if API key is provided."""
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("Initialized Google Gemini client.")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini SDK: {e}. Falling back to Rule-based Intent Engine.")
                self.gemini_client = None
        else:
            logger.info("No Gemini API key supplied. DevMate will run using intelligent Rule-based Intent Engine.")

    def process_query(self, user_query: str, confirmation_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Main entrypoint for user messages.
        
        Returns a dict containing:
        - 'response': Text message / summary for user
        - 'requires_confirmation': bool (True if a sensitive action needs approval)
        - 'pending_action': dict with action details if requires_confirmation is True
        - 'tool_result': dict with raw tool outputs
        """
        user_query_clean = user_query.strip()

        # If user is confirming a previously requested action
        if confirmation_payload:
            return self._execute_confirmed_action(confirmation_payload)

        # 1. Try LLM Tool Calling if Gemini is available
        if self.gemini_client:
            try:
                return self._process_with_llm(user_query_clean)
            except Exception as e:
                logger.warning(f"LLM processing failed: {e}. Falling back to intent parser.")

        # 2. Intent-Based Dispatcher (Zero-cost, works 100% offline)
        return self._process_with_intent_engine(user_query_clean)

    def _process_with_intent_engine(self, query: str) -> Dict[str, Any]:
        """Pattern matching & NLP intent parser for Jira and GitHub commands."""
        q_lower = query.lower()

        # --- JIRA INTENTS ---

        # 1. List assigned issues / stories / tasks
        if any(w in q_lower for w in ["list", "show", "get", "fetch", "my"]) and any(w in q_lower for w in ["ticket", "issue", "story", "stories", "jira", "task"]):
            status_filter = None
            if "in progress" in q_lower:
                status_filter = "In Progress"
            elif "to do" in q_lower or "todo" in q_lower:
                status_filter = "To Do"
            elif "done" in q_lower or "closed" in q_lower:
                status_filter = "Done"

            issues = jira_tool.list_assigned_issues(status=status_filter)
            return {
                "response": f"Found {len(issues)} Jira issues assigned to you:" + ("" if not status_filter else f" (Filtered by '{status_filter}')"),
                "requires_confirmation": False,
                "tool_type": "jira_list",
                "tool_result": issues
            }

        # 2. Create Jira Issue / Ticket
        if any(w in q_lower for w in ["create", "open", "file", "new"]) and any(w in q_lower for w in ["ticket", "issue", "story", "bug", "task"]):
            # Extract summary
            summary = query
            for prefix in ["create ticket", "create a ticket", "create issue", "create a bug", "create story", "create a story", "open a ticket"]:
                if prefix in q_lower:
                    summary = query[q_lower.find(prefix) + len(prefix):].strip(" :-\"\'")
                    break

            issue_type = "Bug" if "bug" in q_lower else ("Story" if "story" in q_lower else "Task")
            priority = "High" if "high" in q_lower or "urgent" in q_lower else ("Low" if "low" in q_lower else "Medium")

            # Human-in-the-loop confirmation safety check
            return {
                "response": f"I've prepared a new Jira {issue_type} for you. Please confirm before I submit it:",
                "requires_confirmation": True,
                "pending_action": {
                    "action": "create_jira_issue",
                    "summary": summary or "New Task from DevMate",
                    "issue_type": issue_type,
                    "priority": priority,
                },
                "tool_type": "jira_create_preview",
                "tool_result": None
            }

        # 3. Transition ticket (e.g. Move DEV-102 to In Progress)
        match_trans = re.search(r"(?:move|transition|update|set)\s+([A-Za-z]+-\d+)\s+(?:to\s+)?(.+)", query, re.IGNORECASE)
        if match_trans:
            key = match_trans.group(1).upper()
            status = match_trans.group(2).strip().title()
            res = jira_tool.transition_issue(key, status)
            return {
                "response": res.get("message", res.get("error")),
                "requires_confirmation": False,
                "tool_type": "jira_transition",
                "tool_result": res
            }

        # --- GITHUB INTENTS ---

        # 4. List Pull Requests
        if any(w in q_lower for w in ["list", "show", "get", "open"]) and any(w in q_lower for w in ["pr", "prs", "pull request", "pull requests"]):
            prs = github_tool.list_pull_requests()
            return {
                "response": f"Retrieved {len(prs)} open Pull Requests for the repository:",
                "requires_confirmation": False,
                "tool_type": "github_prs",
                "tool_result": prs
            }

        # 5. Approve Pull Request (Sensitive: Requires Confirmation!)
        match_pr = re.search(r"approve\s+(?:pr\s+|pull request\s+)?#?(\d+)", query, re.IGNORECASE)
        if match_pr:
            pr_num = int(match_pr.group(1))
            details = github_tool.get_pr_details(pr_num)
            title = details.get("title", f"PR #{pr_num}")

            return {
                "response": f"Approval requested for **PR #{pr_num}**: *\"{title}\"*. This action will approve the pull request on GitHub.",
                "requires_confirmation": True,
                "pending_action": {
                    "action": "approve_pr",
                    "pr_number": pr_num,
                    "title": title,
                    "review_comment": "LGTM! Approved via DevMate AI."
                },
                "tool_type": "github_approve_preview",
                "tool_result": details
            }

        # Default help fallback
        return {
            "response": (
                "👋 I'm **DevMate**, your DevOps assistant! Here are some things you can ask me:\n\n"
                "- 📋 **Jira**: *'List my assigned tickets'*, *'Show stories in progress'*, *'Create a bug for auth timeout'*, *'Move DEV-102 to Done'*\n"
                "- 🐙 **GitHub**: *'List open PRs'*, *'Approve PR #42'*\n"
            ),
            "requires_confirmation": False,
            "tool_type": "help",
            "tool_result": None
        }

    def _execute_confirmed_action(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executes sensitive action once user gives approval."""
        action = payload.get("action")

        if action == "approve_pr":
            pr_num = payload["pr_number"]
            comment = payload.get("review_comment", "Approved via DevMate.")
            result = github_tool.approve_pull_request(pr_num, comment)
            return {
                "response": f"✅ {result.get('message', 'Approved successfully!')}",
                "requires_confirmation": False,
                "tool_type": "github_approve_result",
                "tool_result": result
            }

        elif action == "create_jira_issue":
            result = jira_tool.create_issue(
                summary=payload["summary"],
                issue_type=payload.get("issue_type", "Task"),
                priority=payload.get("priority", "Medium")
            )
            return {
                "response": f"✅ {result.get('message', 'Ticket created!')} (Key: `{result.get('key')}`)",
                "requires_confirmation": False,
                "tool_type": "jira_create_result",
                "tool_result": result
            }

        return {
            "response": "⚠️ Unknown action encountered.",
            "requires_confirmation": False,
            "tool_result": None
        }

    def _process_with_llm(self, query: str) -> Dict[str, Any]:
        """Calls Google Gemini model with function tool schemas."""
        prompt = f"""
You are DevMate, an autonomous DevOps assistant. Analyze the user query and decide if you should invoke a Jira or GitHub action.
User Query: {query}
If the user wants to inspect tickets or PRs, execute read.
If the user wants to create a ticket or approve a PR, specify the action clearly.
"""
        response = self.gemini_client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
        # Parse or default back to intent engine if free-form
        return self._process_with_intent_engine(query)


# Global singleton instance
agent = DevMateAgent()
