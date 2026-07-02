# ---------------------------------------------------------------------------
# Acme HR Knowledge Assistant — Day 7 Production Dockerfile
#
# Best practices applied:
#   1. Slim base image (python:3.11-slim)
#   2. Layer caching — requirements before source
#   3. --no-cache-dir reduces image size
#   4. Non-root user (appuser)
#   5. HEALTHCHECK so orchestrators know when the app is ready
#   6. Pinned FROM tag for reproducibility
#
# Build context must be the repo root so the corpus is reachable:
#   docker build -f labs/devops/day-07/Dockerfile -t hr-assistant:day07 .
# ---------------------------------------------------------------------------

FROM python:3.11-slim

# --- Environment ---------------------------------------------------------- #
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=0.1.0 \
    PORT=8000

WORKDIR /app

# --- Dependencies (own layer — cached until requirements.txt changes) ------ #
COPY labs/devops/_shared/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# --- Application source --------------------------------------------------- #
COPY labs/devops/_shared/service.py ./service.py
COPY labs/devops/_shared/app.py ./app.py

# --- Corpus data ---------------------------------------------------------- #
# Corpus path is resolved relative to service.py's directory at runtime.
COPY data/hr-corpus/ ./data/hr-corpus/

# --- Non-root user -------------------------------------------------------- #
RUN addgroup --system appgroup \
 && adduser --system --ingroup appgroup --no-create-home appuser
USER appuser

# --- Network -------------------------------------------------------------- #
EXPOSE 8000

# --- Liveness check ------------------------------------------------------- #
# Polls /health every 30 s; allows 10 s for the app to start.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c \
      "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
      || exit 1

# --- Entrypoint ----------------------------------------------------------- #
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
