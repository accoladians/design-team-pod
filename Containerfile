# Design Team Pod - Production-Ready Pixel-Perfect Cloning Toolkit
# Security-first containerization with rootless operation and knowledge persistence

FROM python:3.11-slim

# Metadata
LABEL name="design-team-pod"
LABEL version="2.0.0"
LABEL description="Portable Design Team with pixel-perfect cloning tools, AI analysis, and persistent knowledge"
LABEL maintainer="Xwander Platform Team"
LABEL security.capabilities="drop-all"
LABEL security.rootless="true"

# Install system dependencies with minimal attack surface
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core build tools (minimal)
    gcc g++ make \
    # Image processing libraries
    imagemagick libmagickwand-dev \
    libvips-dev libvips-tools \
    # Web automation dependencies
    chromium \
    # Additional image processing
    libpng-dev libjpeg-dev libwebp-dev \
    # Node.js for frontend tools
    nodejs npm \
    # Utilities
    git curl wget ca-certificates \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Node.js dependencies globally (minimal)
RUN npm install -g playwright@1.40.0 \
    && playwright install chromium --with-deps \
    && npm cache clean --force

# Create app structure and user BEFORE copying files
RUN groupadd -r designteam --gid 1000 && \
    useradd -r -u 1000 -g designteam -d /app -s /bin/bash -c "Design Team User" designteam && \
    mkdir -p /app/{tools,knowledge,api,workspace,cache,config} && \
    mkdir -p /app/workspace/{input,output,cache,temp,projects} && \
    chown -R designteam:designteam /app

WORKDIR /app

# Install Python dependencies (optimized layer caching)
COPY requirements.txt /app/
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application files
COPY tools/ /app/tools/
COPY knowledge/ /app/knowledge/
COPY api/ /app/api/
COPY config/ /app/config/

# Create convenience scripts
RUN echo '#!/bin/bash\nexec python3 /app/tools/visual_diff.py "$@"' > /app/tools/visual-diff && \
    echo '#!/bin/bash\nexec python3 /app/tools/scrape_content.py "$@"' > /app/tools/scrape-content && \
    echo '#!/bin/bash\nexec python3 /app/tools/ai_analyzer.py "$@"' > /app/tools/ai-analyze && \
    chmod +x /app/tools/visual-diff /app/tools/scrape-content /app/tools/ai-analyze

# Final ownership and permissions
RUN chown -R designteam:designteam /app && \
    chmod +x /app/tools/*.py /app/api/*.py && \
    chmod 755 /app/workspace/*

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Switch to non-root user
USER designteam

# Environment configuration
ENV PYTHONPATH="/app/tools:/app/api:/home/designteam/.local/lib/python3.11/site-packages"
ENV PATH="/app/tools:/home/designteam/.local/bin:$PATH"
ENV HOME="/app"
ENV USER="designteam"
ENV WORKSPACE_DIR="/app/workspace"
ENV TOOLS_DIR="/app/tools"
ENV KNOWLEDGE_DIR="/app/knowledge"
ENV CONFIG_DIR="/app/config"

# API configuration
ENV API_HOST="0.0.0.0"
ENV API_PORT="8080"
ENV API_WORKERS="1"
ENV LOG_LEVEL="info"

# Tool configuration
ENV IMAGEMAGICK_BINARY="convert"
ENV CHROMIUM_BINARY="/usr/bin/chromium-browser"
ENV PLAYWRIGHT_BROWSERS_PATH="/home/designteam/.cache/ms-playwright"

# Expose API port
EXPOSE 8080

# Volume mount points for data persistence
VOLUME ["/app/workspace", "/app/knowledge", "/app/config"]

# Default command - start API server with proper signal handling
CMD ["python3", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]