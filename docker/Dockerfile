# ==============================================================================
# Stage 1: Build & Dependencies Layer
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies to a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ==============================================================================
# Stage 2: Minimal Production Runtime
# ==============================================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Environment configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true

# Copy installed virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create a non-root system user for security compliance
RUN groupadd -r devmate && useradd -r -g devmate -d /app devmateuser && \
    chown -R devmateuser:devmate /app

# Copy application source code
COPY --chown=devmateuser:devmate app/ ./app
COPY --chown=devmateuser:devmate tests/ ./tests
COPY --chown=devmateuser:devmate .env.example ./.env.example

# Drop root privileges
USER devmateuser

# Expose Streamlit default port
EXPOSE 8501

# Container healthcheck instruction
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# Launch Streamlit app
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
