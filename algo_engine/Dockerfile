# ==============================================================================
# TLCS Black Box Signal Engine Daemon v2.0 - Production Dockerfile
# ==============================================================================
FROM python:3.11-slim AS runtime

# Set environment variables for performance and clean logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    TZ=Asia/Kolkata

WORKDIR /app

# Install minimal system dependencies (curl for healthchecks & ca-certificates for SSL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Create non-root system user and directories
RUN useradd -m -u 1000 tlcs && \
    mkdir -p /app/algo_engine/data /app/algo_engine/logs && \
    chown -R tlcs:tlcs /app

# Copy application source code
COPY . /app/algo_engine

# Ensure correct file permissions
RUN chown -R tlcs:tlcs /app/algo_engine && \
    chmod +x /app/algo_engine/run_daemon.py

# Switch to non-root user
USER tlcs

# Healthcheck to verify Python runtime responsiveness
HEALTHCHECK --interval=60s --timeout=10s --start-period=15s --retries=3 \
    CMD python3 -c "import algo_engine; sys_exit = 0" || exit 1

# Default execution: Standalone Engine Daemon
ENTRYPOINT ["python3", "/app/algo_engine/run_daemon.py"]
CMD []
