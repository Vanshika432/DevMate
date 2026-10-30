"""GitHub Tool Connector for DevMate.

Provides methods to search pull requests, fetch diff details,
and approve pull requests.
Supports real PyGithub REST API and an in-memory Mock Mode.
"""

from typing import Dict, Any, List, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class GitHubTool:
    """Manages GitHub repository interactions with mock fallback."""

    def __init__(self, mock_mode: Optional[bool] = None):
        self.mock_mode = settings.MOCK_MODE if mock_mode is None else mock_mode
        self.gh_client = None

        if not self.mock_mode and settings.GITHUB_TOKEN:
            try:
                from github import Github, Auth
                auth = Auth.Token(settings.GITHUB_TOKEN)
                self.gh_client = Github(auth=auth)
                logger.info("Connected to GitHub API successfully.")
            except Exception as e:
                logger.warning(f"Failed to connect to GitHub API: {e}. Falling back to Mock Mode.")
                self.mock_mode = True
        else:
            self.mock_mode = True

        # In-memory mock pull requests
        self._mock_prs: List[Dict[str, Any]] = [
            {
                "number": 42,
                "title": "feat(auth): add OAuth2 refresh token rotation",
                "repo": "Vanshika432/DevMate",
                "state": "open",
                "author": "dev-teammate",
                "created_at": "2026-10-29",
                "html_url": "https://github.com/Vanshika432/DevMate/pull/42",
                "reviews": [],
                "diff_summary": "+45 lines, -12 lines across 3 files",
            },
            {
                "number": 43,
                "title": "fix(ci): fix flaky integration test for Jira webhook",
                "repo": "Vanshika432/DevMate",
                "state": "open",
                "author": "ci-bot",
                "created_at": "2026-10-30",
                "html_url": "https://github.com/Vanshika432/DevMate/pull/43",
                "reviews": [],
                "diff_summary": "+10 lines, -5 lines in tests/test_jira.py",
            },
        ]

    def _resolve_repo(self, repo_name: Optional[str]) -> str:
        return repo_name or settings.GITHUB_DEFAULT_REPO or "Vanshika432/DevMate"

    def list_pull_requests(self, repo_name: Optional[str] = None, state: str = "open") -> List[Dict[str, Any]]:
        """List pull requests for a repository."""
        target_repo = self._resolve_repo(repo_name)

        if self.mock_mode or not self.gh_client:
            return [
                pr for pr in self._mock_prs
                if pr["state"].lower() == state.lower()
            ]

        try:
            repo = self.gh_client.get_repo(target_repo)
            pulls = repo.get_pulls(state=state, sort="created", direction="desc")
            return [
                {
                    "number": pr.number,
                    "title": pr.title,
                    "repo": target_repo,
                    "state": pr.state,
                    "author": pr.user.login,
                    "created_at": pr.created_at.strftime("%Y-%m-%d"),
                    "html_url": pr.html_url,
                }
                for pr in pulls[:10]
            ]
        except Exception as e:
            logger.error(f"Error fetching PRs from GitHub: {e}")
            return [{"error": str(e)}]

    def get_pr_details(self, pr_number: int, repo_name: Optional[str] = None) -> Dict[str, Any]:
        """Fetch detailed information about a specific PR."""
        target_repo = self._resolve_repo(repo_name)

        if self.mock_mode or not self.gh_client:
            match = next((pr for pr in self._mock_prs if pr["number"] == pr_number), None)
            if match:
                return match
            return {"error": f"Pull request #{pr_number} not found in {target_repo}."}

        try:
            repo = self.gh_client.get_repo(target_repo)
            pr = repo.get_pull(pr_number)
            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "repo": target_repo,
                "state": pr.state,
                "author": pr.user.login,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files,
                "html_url": pr.html_url,
                "mergeable": pr.mergeable,
            }
        except Exception as e:
            logger.error(f"Error fetching PR #{pr_number}: {e}")
            return {"error": str(e)}

    def approve_pull_request(
        self,
        pr_number: int,
        review_comment: str = "LGTM! Approved via DevMate AI.",
        repo_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Approve a GitHub Pull Request with a review comment."""
        target_repo = self._resolve_repo(repo_name)

        if self.mock_mode or not self.gh_client:
            for pr in self._mock_prs:
                if pr["number"] == pr_number:
                    pr["reviews"].append({
                        "state": "APPROVED",
                        "comment": review_comment,
                        "reviewer": "Vanshika Rathore (DevMate)"
                    })
                    return {
                        "success": True,
                        "pr_number": pr_number,
                        "repo": target_repo,
                        "status": "APPROVED",
                        "comment": review_comment,
                        "message": f"Successfully approved PR #{pr_number} on {target_repo}!"
                    }
            return {"success": False, "error": f"Pull request #{pr_number} not found."}

        try:
            repo = self.gh_client.get_repo(target_repo)
            pr = repo.get_pull(pr_number)
            pr.create_review(body=review_comment, event="APPROVE")
            return {
                "success": True,
                "pr_number": pr_number,
                "repo": target_repo,
                "status": "APPROVED",
                "comment": review_comment,
                "message": f"Successfully approved PR #{pr_number} in {target_repo}."
            }
        except Exception as e:
            logger.error(f"Error approving PR #{pr_number}: {e}")
            return {"success": False, "error": str(e)}


# Global singleton instance
github_tool = GitHubTool()

