# ============================================================
# Stage 1: Build dependencies
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build deps
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/build/deps -r requirements.txt

# ============================================================
# Stage 2: Runtime image
# ============================================================
FROM python:3.11-slim AS runtime

# TODO: Add security scanning step (trivy, grype) in CI before pushing
# TODO: Consider distroless base for production

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /build/deps /usr/local/lib/python3.11/site-packages/

# Copy application code
# NOTE: In a real pipeline, copy only what's needed
COPY . .

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Environment defaults (override at runtime)
ENV LLM_PROVIDER=mock \
    PORT=8000 \
    LOG_LEVEL=INFO \
    APP_VERSION=capstone

EXPOSE 8000

# TODO: Replace with your actual app entrypoint
# For the shared app:
CMD ["python", "-m", "uvicorn", "labs.devops._shared.app:app", "--host", "0.0.0.0", "--port", "8000"]
