# Bear Alarm - Dexcom Glucose Monitoring
# Multi-stage build for smaller image size

FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .


# Final stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies for audio playback
RUN apt-get update && apt-get install -y --no-install-recommends \
    libasound2 \
    libasound2-plugins \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/

# Create directory for alert sounds
RUN mkdir -p /app/alerts

# Run as non-root user for security
RUN useradd -m -u 1000 bearalarm && \
    chown -R bearalarm:bearalarm /app
USER bearalarm

# Health check
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "python.*main.py" || exit 1

# Run the application
CMD ["python", "-m", "src.main"]

