"""Application configuration settings using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_ENV: str = "development"
    STREAMLIT_PORT: int = 8501
    MOCK_MODE: bool = True

    # LLM
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # GitHub
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_DEFAULT_REPO: Optional[str] = None

    # Jira
    JIRA_SERVER_URL: Optional[str] = None
    JIRA_EMAIL: Optional[str] = None
    JIRA_API_TOKEN: Optional[str] = None
    JIRA_PROJECT_KEY: Optional[str] = None


settings = Settings()

