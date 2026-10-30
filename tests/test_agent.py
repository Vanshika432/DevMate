"""Unit tests for DevMate AI Agent and Human-in-the-Loop confirmations."""

import unittest
from app.agent import DevMateAgent


class TestDevMateAgent(unittest.TestCase):

    def setUp(self):
        self.agent = DevMateAgent()

    def test_list_jira_issues_intent(self):
        result = self.agent.process_query("list my assigned tickets on jira")
        self.assertEqual(result["tool_type"], "jira_list")
        self.assertFalse(result["requires_confirmation"])
        self.assertGreaterEqual(len(result["tool_result"]), 3)

    def test_filter_jira_issues_intent(self):
        result = self.agent.process_query("show stories in progress")
        self.assertEqual(result["tool_type"], "jira_list")
        self.assertFalse(result["requires_confirmation"])
        # All returned tickets should have status In Progress
        for item in result["tool_result"]:
            self.assertEqual(item["status"].lower(), "in progress")

    def test_create_ticket_requires_confirmation(self):
        query = "Create a bug for database timeout on login"
        result = self.agent.process_query(query)
        self.assertTrue(result["requires_confirmation"])
        self.assertEqual(result["pending_action"]["action"], "create_jira_issue")
        self.assertEqual(result["pending_action"]["issue_type"], "Bug")

        # Now simulate user confirming
        confirm_res = self.agent.process_query("Confirm", confirmation_payload=result["pending_action"])
        self.assertFalse(confirm_res["requires_confirmation"])
        self.assertTrue(confirm_res["tool_result"]["success"])

    def test_list_github_prs_intent(self):
        result = self.agent.process_query("show open pull requests")
        self.assertEqual(result["tool_type"], "github_prs")
        self.assertFalse(result["requires_confirmation"])
        self.assertGreaterEqual(len(result["tool_result"]), 2)

    def test_approve_pr_requires_confirmation(self):
        result = self.agent.process_query("Approve PR #42 on git")
        self.assertTrue(result["requires_confirmation"])
        self.assertEqual(result["pending_action"]["action"], "approve_pr")
        self.assertEqual(result["pending_action"]["pr_number"], 42)

        # Confirm approval
        confirm_res = self.agent.process_query("Yes", confirmation_payload=result["pending_action"])
        self.assertFalse(confirm_res["requires_confirmation"])
        self.assertEqual(confirm_res["tool_result"]["status"], "APPROVED")


if __name__ == "__main__":
    unittest.main()
