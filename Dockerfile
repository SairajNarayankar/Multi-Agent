# Dockerfile (backend)

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agents/ ./agents/
COPY api/ ./api/
COPY config/ ./config/
COPY db/ ./db/
COPY tools/ ./tools/
COPY tests/ ./tests/
COPY .env .

# Create non-root user
RUN useradd --create-home appuser
USER appuser

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]