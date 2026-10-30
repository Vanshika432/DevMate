"""Jira Tool Connector for DevMate.

Provides methods to search, create, and transition Jira issues.
Supports real Atlassian Jira Cloud REST API and an in-memory Mock Mode.
"""

from typing import Dict, Any, List, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class JiraTool:
    """Manages Jira interactions with automatic fallback to mock data."""

    def __init__(self, mock_mode: Optional[bool] = None):
        self.mock_mode = settings.MOCK_MODE if mock_mode is None else mock_mode
        self.client = None

        if not self.mock_mode and settings.JIRA_SERVER_URL and settings.JIRA_API_TOKEN:
            try:
                from jira import JIRA
                self.client = JIRA(
                    server=settings.JIRA_SERVER_URL,
                    basic_auth=(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN)
                )
                logger.info("Connected to Jira Cloud instance successfully.")
            except Exception as e:
                logger.warning(f"Failed to connect to Jira Cloud: {e}. Falling back to Mock Mode.")
                self.mock_mode = True
        else:
            self.mock_mode = True

        # In-memory mock database for offline / demo mode
        self._mock_issues: List[Dict[str, Any]] = [
            {
                "key": "DEV-101",
                "summary": "Fix race condition in user authentication webhook",
                "status": "In Progress",
                "priority": "High",
                "issue_type": "Bug",
                "assignee": "Vanshika Rathore",
                "created": "2026-10-28",
            },
            {
                "key": "DEV-102",
                "summary": "Implement Redis caching layer for GitHub API rate limits",
                "status": "To Do",
                "priority": "Medium",
                "issue_type": "Story",
                "assignee": "Vanshika Rathore",
                "created": "2026-10-29",
            },
            {
                "key": "DEV-103",
                "summary": "Upgrade Docker base image to distroless for security hardening",
                "status": "Code Review",
                "priority": "Low",
                "issue_type": "Task",
                "assignee": "Vanshika Rathore",
                "created": "2026-10-30",
            },
        ]

    def list_assigned_issues(self, assignee: str = "currentUser()", status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Jira issues assigned to a specific user or the current user."""
        if self.mock_mode or not self.client:
            results = self._mock_issues
            if status:
                results = [i for i in results if i["status"].lower() == status.lower()]
            return results

        try:
            jql = f"assignee = {assignee}"
            if status:
                jql += f" AND status = '{status}'"
            issues = self.client.search_issues(jql, maxResults=20)
            return [
                {
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name,
                    "priority": getattr(issue.fields.priority, "name", "None"),
                    "issue_type": issue.fields.issuetype.name,
                    "assignee": getattr(issue.fields.assignee, "displayName", "Unassigned"),
                    "created": issue.fields.created,
                }
                for issue in issues
            ]
        except Exception as e:
            logger.error(f"Error querying Jira: {e}")
            return [{"error": str(e)}]

    def create_issue(
        self,
        summary: str,
        description: str = "",
        issue_type: str = "Story",
        priority: str = "Medium",
        project_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new Jira issue/ticket."""
        proj = project_key or settings.JIRA_PROJECT_KEY or "DEV"

        if self.mock_mode or not self.client:
            new_key = f"{proj}-{len(self._mock_issues) + 101}"
            new_issue = {
                "key": new_key,
                "summary": summary,
                "description": description,
                "status": "To Do",
                "priority": priority,
                "issue_type": issue_type,
                "assignee": "Vanshika Rathore",
                "created": "Just now",
            }
            self._mock_issues.append(new_issue)
            return {
                "success": True,
                "key": new_key,
                "summary": summary,
                "status": "To Do",
                "message": f"Ticket {new_key} successfully created."
            }

        try:
            issue_dict = {
                "project": {"key": proj},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
                "priority": {"name": priority},
            }
            created = self.client.create_issue(fields=issue_dict)
            return {
                "success": True,
                "key": created.key,
                "summary": summary,
                "message": f"Ticket {created.key} created in Jira."
            }
        except Exception as e:
            logger.error(f"Error creating Jira issue: {e}")
            return {"success": False, "error": str(e)}

    def transition_issue(self, issue_key: str, transition_name: str) -> Dict[str, Any]:
        """Update Jira issue status (e.g., 'In Progress', 'Done', 'Code Review')."""
        if self.mock_mode or not self.client:
            for issue in self._mock_issues:
                if issue["key"].upper() == issue_key.upper():
                    old_status = issue["status"]
                    issue["status"] = transition_name
                    return {
                        "success": True,
                        "key": issue_key,
                        "old_status": old_status,
                        "new_status": transition_name,
                        "message": f"Updated {issue_key} from '{old_status}' to '{transition_name}'."
                    }
            return {"success": False, "error": f"Ticket {issue_key} not found."}

        try:
            transitions = self.client.transitions(issue_key)
            match = next((t for t in transitions if t["name"].lower() == transition_name.lower()), None)
            if not match:
                available = [t["name"] for t in transitions]
                return {
                    "success": False,
                    "error": f"Invalid transition '{transition_name}'. Available transitions: {available}"
                }
            self.client.transition_issue(issue_key, match["id"])
            return {
                "success": True,
                "key": issue_key,
                "new_status": transition_name,
                "message": f"Ticket {issue_key} transitioned to '{transition_name}'."
            }
        except Exception as e:
            logger.error(f"Error transitioning Jira issue: {e}")
            return {"success": False, "error": str(e)}


# Global singleton instance
jira_tool = JiraTool()
