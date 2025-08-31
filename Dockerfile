# Dockerfile for Garmin Dashboard
# Multi-stage build for optimized production deployment

# Build stage - Install dependencies and compile
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for parsing libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Production stage - Minimal runtime image
FROM python:3.11-slim as production

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r garmin && useradd -r -g garmin garmin

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY app/ ./app/
COPY ingest/ ./ingest/
COPY cli/ ./cli/
COPY pages/ ./pages/
COPY garmin_client/ ./garmin_client/
COPY run_tests.py .

# Create data directories with proper permissions
RUN mkdir -p /data /app/activities /home/garmin && \
    chown -R garmin:garmin /app /data /home/garmin

# Create health check script
RUN echo '#!/bin/bash\ncurl -f http://localhost:8050/ || exit 1' > /healthcheck.sh && \
    chmod +x /healthcheck.sh

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Switch to non-root user
USER garmin

# Environment variables for production
ENV PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL="sqlite:///data/garmin_dashboard.db" \
    DASH_DEBUG="False" \
    HOST="0.0.0.0" \
    PORT="8050"

# Expose port
EXPOSE 8050

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /healthcheck.sh

# Default command runs the web application
CMD ["python", "/app/app/dash_app.py"]

# Labels for better Docker image management
LABEL maintainer="Garmin Dashboard" \
      description="Local-first Garmin activity dashboard with Dash and Plotly" \
      version="1.0.0" \
      org.opencontainers.image.source="https://github.com/your-repo/garmin-dashboard" \
      org.opencontainers.image.title="Garmin Dashboard" \
      org.opencontainers.image.description="Private, local-first dashboard for Garmin activities"