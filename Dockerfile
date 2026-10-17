# ============================================================
# National Public Grievance Portal — Production Dockerfile
# Target: Render.com Docker Web Service
# Architecture: Python 3.10 + Node.js 20 (single container)
# Services: FastAPI AI Engine (:8000) + Express API (:3000)
# ============================================================

FROM python:3.10-slim

# ── Environment ──────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODE_VERSION=20.x \
    PORT=3000 \
    NODE_ENV=production

WORKDIR /app

# ── System deps + Node.js installation ───────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies (cached as a separate layer) ─────────
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ── Node.js dependencies ──────────────────────────────────────
COPY package*.json ./
RUN npm install --production --no-audit --no-fund

# ── Application source code ───────────────────────────────────
COPY . .

# ── Verify dataset & ML models ────────────────────────────────
# Uses standalone python script to avoid Dockerfile inline parsing issues
RUN python prepare_models.py

# ── Ensure start script is executable (normalize CRLF) ────────
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh

# ── Expose ports ──────────────────────────────────────────────
# Render maps the public HTTPS port to $PORT (3000)
# Port 8000 is internal only (FastAPI)
EXPOSE 3000

# ── Entrypoint: start both services ──────────────────────────
CMD ["./start.sh"]
