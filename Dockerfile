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

# ── Python dependencies (heavy — cached as a separate layer) ──
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ── Node.js dependencies ──────────────────────────────────────
COPY package*.json ./
RUN npm install --production --no-audit --no-fund

# ── Application source code ───────────────────────────────────
COPY . .

# ── Generate dataset & train ML models (baked into image) ─────
# This is skipped if saved_models/ already has .pkl files.
# Prevents full retraining on every deploy restart.
RUN python -c "
from pathlib import Path
from config import MODELS_DIR, DATA_DIR
clf_exists = (MODELS_DIR / 'baseline_classifier.pkl').exists()
prio_exists = (MODELS_DIR / 'priority_predictor.pkl').exists()
data_exists = (DATA_DIR / 'train.json').exists()
if not data_exists:
    print('[Build] Generating dataset...')
    import subprocess
    subprocess.run(['python', 'data_generator.py'], check=True)
if not clf_exists or not prio_exists:
    print('[Build] Training ML models (first build only)...')
    import subprocess
    subprocess.run(['python', 'train_models.py'], check=True)
else:
    print('[Build] Saved models found — skipping training.')
"

# ── Ensure start script is executable ─────────────────────────
RUN chmod +x start.sh

# ── Expose ports ──────────────────────────────────────────────
# Render maps the public HTTPS port to $PORT (3000)
# Port 8000 is internal only (FastAPI)
EXPOSE 3000

# ── Entrypoint: start both services ──────────────────────────
CMD ["./start.sh"]
