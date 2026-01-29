# Platform Dockerfile
# Multi-stage build for development and production

FROM node:20-slim AS ui-deps
WORKDIR /app/ui
COPY ui/package.json ui/package-lock.json* ./
RUN npm install

FROM node:20-slim AS ui-build
WORKDIR /app/ui
COPY --from=ui-deps /app/ui/node_modules ./node_modules
COPY ui/ ./
RUN npm run build

# Main application image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for development mode
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy Python project files
COPY pyproject.toml ./
COPY README.md ./
COPY config.toml ./
COPY alembic.ini ./
COPY backend/ ./backend/

# Install Python dependencies
RUN uv sync

# Copy UI files
COPY ui/ ./ui/

# Install UI dependencies (for development mode)
WORKDIR /app/ui
RUN npm install

WORKDIR /app

# Copy built UI for production
COPY --from=ui-build /app/ui/dist ./ui/dist

# Copy nginx configuration
COPY nginx.conf ./nginx.conf
COPY nginx.prod.conf ./nginx.prod.conf

# Copy startup script and fix line endings (CRLF -> LF) for Linux
COPY start.sh /opt/start.sh
RUN sed -i 's/\r$//' /opt/start.sh && chmod +x /opt/start.sh

# Create nginx directories
RUN mkdir -p /var/log/nginx /var/lib/nginx/body /run

# Configure nginx
RUN rm -f /etc/nginx/sites-enabled/default
RUN echo "pid /run/nginx.pid;" > /etc/nginx/nginx.conf && \
    echo "events { worker_connections 1024; }" >> /etc/nginx/nginx.conf && \
    echo "http {" >> /etc/nginx/nginx.conf && \
    echo "    include /etc/nginx/mime.types;" >> /etc/nginx/nginx.conf && \
    echo "    default_type application/octet-stream;" >> /etc/nginx/nginx.conf && \
    echo "    sendfile on;" >> /etc/nginx/nginx.conf && \
    echo "    keepalive_timeout 65;" >> /etc/nginx/nginx.conf && \
    echo "    include /app/nginx*.conf;" >> /etc/nginx/nginx.conf && \
    echo "}" >> /etc/nginx/nginx.conf

# Environment variables
ENV FLASK_ENV=development
ENV DATABASE_HOST=platform_db
ENV DATABASE_PORT=5432
ENV DATABASE_NAME=platform
ENV DATABASE_USER=platform
ENV DATABASE_PASSWORD=platform_dev_password

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Start services (use bash explicitly so CRLF line endings don't break exec)
CMD ["/bin/bash", "/opt/start.sh"]
