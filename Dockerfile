# Multi-stage build for Figma MCP Bridge
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python requirements
COPY server/requirements.txt /app/server/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r server/requirements.txt

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest>=7.0.0 \
    pytest-asyncio>=0.23.0 \
    black>=23.0.0 \
    ruff>=0.1.0 \
    mypy>=1.0.0

# Copy source code
COPY . /app/

# Install Node.js for Style Dictionary
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install Style Dictionary
RUN npm install -g style-dictionary

# Make CLI executable
RUN chmod +x /app/cli/figma_ds_sync.py

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Default command
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Production stage
FROM base as production

# Copy only necessary files
COPY server/ /app/server/
COPY cli/ /app/cli/
COPY figma-agent.yaml /app/
COPY style-dictionary.config.js /app/

# Create non-root user
RUN groupadd -r figma && useradd -r -g figma figma
RUN chown -R figma:figma /app
USER figma

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Production command
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]