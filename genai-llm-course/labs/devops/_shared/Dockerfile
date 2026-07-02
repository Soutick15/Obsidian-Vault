FROM python:3.11-slim

# Prevents .pyc files and ensures stdout/stderr are unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer cache friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the shared service files
COPY service.py .
COPY app.py .

# Copy the HR corpus (relative to repo root at build time)
# Build context must be the repo root:
#   docker build -f labs/devops/_shared/Dockerfile .
COPY data/hr-corpus/ ./data/hr-corpus/

EXPOSE 8000

# app.py imports service.py from the same directory; run from /app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
