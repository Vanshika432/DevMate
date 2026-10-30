"""Application configuration settings with zero-dependency fallback."""

import os
from typing import Optional


class Settings:
    """Lightweight settings loader using environment variables."""

    def __init__(self):
        # Read .env file if present
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())

        # App settings
        self.APP_ENV: str = os.getenv("APP_ENV", "development")
        self.STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))
        self.MOCK_MODE: bool = os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes")

        # LLM
        self.GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
        self.GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        # GitHub
        self.GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
        self.GITHUB_DEFAULT_REPO: Optional[str] = os.getenv("GITHUB_DEFAULT_REPO", "Vanshika432/DevMate")

        # Jira
        self.JIRA_SERVER_URL: Optional[str] = os.getenv("JIRA_SERVER_URL")
        self.JIRA_EMAIL: Optional[str] = os.getenv("JIRA_EMAIL")
        self.JIRA_API_TOKEN: Optional[str] = os.getenv("JIRA_API_TOKEN")
        self.JIRA_PROJECT_KEY: Optional[str] = os.getenv("JIRA_PROJECT_KEY", "DEV")


settings = Settings()


