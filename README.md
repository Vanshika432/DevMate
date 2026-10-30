# DevMate: AI-Powered DevOps & Engineering Assistant

An intelligent, production-ready DevOps chatbot that automates engineering workflows across **Jira** and **GitHub** using natural language, structured tool calling, Docker, and CI/CD.

## 🚀 Key Features

- **Jira Operations**:
  - Search and list assigned issues / backlog stories.
  - Create new tickets with summaries, descriptions, issue types, and priorities.
  - Transition ticket status (e.g., In Progress, Code Review, Done).
- **GitHub Operations**:
  - List and search open pull requests and issues.
  - Inspect PR details and review comments.
  - Review and approve Pull Requests with confirmation safety checks.
- **Enterprise-Ready Design**:
  - **Human-In-The-Loop**: Destructive actions (e.g. approving a PR) require user confirmation before execution.
  - **Zero-Cost Friendly**: Runs with free-tier Gemini API and includes a full **Mock Mode** for testing without active Jira/GitHub credentials.
  - **Containerized**: Multi-stage Dockerfile and Docker Compose.
  - **CI/CD**: GitHub Actions pipeline covering linting, test suites, and Docker image builds.

## 📂 Project Layout

```
DevMate/
├── .github/workflows/       # GitHub Actions CI/CD pipelines
├── app/
│   ├── config.py           # Environment configuration
│   ├── main.py             # Streamlit Chat Application
│   ├── agent.py            # AI Agent & LLM tool-calling logic
│   └── tools/
│       ├── github_tool.py  # GitHub integration & mock fallback
│       └── jira_tool.py    # Jira integration & mock fallback
├── docker/
│   ├── Dockerfile          # Multi-stage production container build
│   └── docker-compose.yml  # Local one-command development stack
├── tests/                  # Pytest unit & integration test suites
├── requirements.txt        # Production & testing dependencies
└── .env.example            # Environment variables template
```

## 🛠️ Quick Start

### 1. Run with Docker (Recommended for Production)

```bash
docker compose up --build
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

### 2. Run Locally with Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

### 3. Run Automated Tests

```bash
PYTHONPATH=. python3 -m unittest discover tests
```

---

## 🔄 CI/CD Pipeline

The project includes an enterprise-grade **GitHub Actions CI/CD pipeline** ([`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml)) that automatically triggers on every push and pull request:
1. **Automated Testing Job**: Sets up Python 3.11 with pip caching and runs all unit tests for Jira, GitHub, and Agent logic.
2. **Docker Build Job**: Uses Docker Buildx with GitHub Actions Layer Caching to ensure the multi-stage Docker image compiles without errors.

