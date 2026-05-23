# syntax=docker/dockerfile:1
#
# Multi-stage build:
#   Stage 1 (frontend-build): Compile the Vue 3 SPA with Node.js
#   Stage 2 (python-deps):    Build Python dependencies in a venv
#   Stage 3 (app):            Python/Gunicorn production server
#
# Single image works on both desktop and Raspberry Pi.
# GPIO behaviour is controlled at runtime via ENABLE_GPIO env var:
#   ENABLE_GPIO=false  → GPIO routes disabled, mock fallback used (desktop)
#   ENABLE_GPIO=true   → GPIO routes active (Raspberry Pi)
#
# Published to GitHub Container Registry by CI on every push to main.
# Pull with:  docker pull ghcr.io/benitocalcanho/invisible-key:latest

# ════════════════════════════════════════════════════════════════════════════
# Stage 1 — Build the Vue 3 frontend
# ════════════════════════════════════════════════════════════════════════════
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

# Install dependencies first (better layer caching)
COPY frontend/package*.json ./
RUN npm ci

# Copy source and build
COPY frontend/ ./
RUN npm run build
# Output: /app/frontend/dist/

# ════════════════════════════════════════════════════════════════════════════
# Stage 2 — Build Python dependencies
# ════════════════════════════════════════════════════════════════════════════
FROM python:3.11-slim AS python-deps

WORKDIR /app
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Build packages are intentionally kept out of the final runtime image.
# Pillow may compile from source on linux/arm/v7, so zlib/jpeg/webp headers
# must be available in this builder stage.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libc6-dev \
    zlib1g-dev \
    libjpeg62-turbo-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
COPY backend/requirements-pi.txt ./backend/requirements-pi.txt

# Always install requirements-pi.txt (includes gpiozero). gpiozero uses
# MockFactory automatically on non-Pi hardware, so it is safe everywhere.
RUN python -m venv "$VIRTUAL_ENV" && \
    pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir --prefer-binary -r backend/requirements-pi.txt

# Install the ngrok agent during the image build. This keeps slow or flaky
# runtime DNS/downloads off the Raspberry Pi when the tunnel starts.
RUN python -c "from pyngrok import installer; installer.install_ngrok('/usr/local/bin/ngrok')"

# ════════════════════════════════════════════════════════════════════════════
# Stage 3 — Production image (runs on Pi or desktop)
# ════════════════════════════════════════════════════════════════════════════
FROM python:3.11-slim

# Prevent .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# ── Runtime system packages ─────────────────────────────────────────────────
# bash/procps       : needed by stop_ngrok.sh
# zlib/jpeg/webp    : runtime libraries for Pillow image optimization
# network-manager   : provides nmcli for WiFi management via host NetworkManager
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    procps \
    zlib1g \
    libjpeg62-turbo \
    libwebp7 \
    network-manager \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-deps /opt/venv /opt/venv
COPY --from=python-deps /usr/local/bin/ngrok /usr/local/bin/ngrok

# ── Application source ───────────────────────────────────────────────────────
COPY backend/ ./backend/
COPY scripts/ ./scripts/

# Flask expects the built Vue SPA at ../frontend/dist/ relative to backend/app.py
COPY --from=frontend-build /app/frontend/dist ./frontend/dist/

# ── Persistent directories ───────────────────────────────────────────────────
# These are mounted as Docker named volumes at runtime (see docker-compose.yml)
# Flask-SQLAlchemy 3.x resolves sqlite:///data/invisible_key.db relative to instance_path
RUN mkdir -p \
    /app/backend/instance/data \
    /app/backend/uploads \
    /app/config

# ── Runtime ──────────────────────────────────────────────────────────────────
EXPOSE 5000
WORKDIR /app/backend

# Single worker to avoid multiple ngrok tunnels on startup.
# Threads allow concurrent requests (e.g. GPIO + audit log simultaneously).
# --timeout 120 accommodates calendar sync on slow Pi hardware.
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "1", \
     "--threads", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "app:create_app()"]
