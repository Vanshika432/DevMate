"""Unit tests for Jira and GitHub tools (Mock and Fallback engine)."""

import unittest
from app.tools.jira_tool import JiraTool
from app.tools.github_tool import GitHubTool


class TestDevMateTools(unittest.TestCase):

    def test_jira_list_assigned_issues(self):
        jira = JiraTool(mock_mode=True)
        issues = jira.list_assigned_issues()
        self.assertGreaterEqual(len(issues), 3)
        self.assertTrue(any(i["key"] == "DEV-101" for i in issues))

    def test_jira_create_issue(self):
        jira = JiraTool(mock_mode=True)
        res = jira.create_issue(
            summary="Automate end-to-end smoke testing",
            description="Verify health endpoints after each deployment",
            issue_type="Task",
            priority="High"
        )
        self.assertTrue(res["success"])
        self.assertIn("DEV-", res["key"])

        # Verify it appears in search
        issues = jira.list_assigned_issues()
        self.assertTrue(any(i["key"] == res["key"] for i in issues))

    def test_jira_transition_issue(self):
        jira = JiraTool(mock_mode=True)
        res = jira.transition_issue("DEV-102", "In Progress")
        self.assertTrue(res["success"])
        self.assertEqual(res["new_status"], "In Progress")

    def test_github_list_prs(self):
        gh = GitHubTool(mock_mode=True)
        prs = gh.list_pull_requests(state="open")
        self.assertGreaterEqual(len(prs), 2)
        self.assertEqual(prs[0]["number"], 42)

    def test_github_get_pr_details(self):
        gh = GitHubTool(mock_mode=True)
        details = gh.get_pr_details(42)
        self.assertEqual(details["number"], 42)
        self.assertIn("OAuth2", details["title"])

    def test_github_approve_pr(self):
        gh = GitHubTool(mock_mode=True)
        res = gh.approve_pull_request(
            pr_number=42,
            review_comment="Code is clean and tests pass. Approved!"
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "APPROVED")


if __name__ == "__main__":
    unittest.main()

