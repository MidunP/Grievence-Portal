#!/bin/bash
# ============================================================
# National Public Grievance Portal — Production Startup Script
# Starts FastAPI AI engine first, waits for readiness,
# then starts Express backend in the foreground.
# ============================================================
set -e

echo "═══════════════════════════════════════════════════════════"
echo "  National Public Grievance Portal — Starting Services"
echo "═══════════════════════════════════════════════════════════"

# ── 1. Launch FastAPI AI Microservice in background ──────────
echo "[1/3] Starting AI Inference Engine (FastAPI on :8000)..."
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --workers 1 &
FASTAPI_PID=$!
echo "      FastAPI PID: $FASTAPI_PID"

# ── 2. Wait until FastAPI is healthy (up to 90 seconds) ──────
echo "[2/3] Waiting for AI Engine to warm up (model loading)..."
MAX_WAIT=90
ELAPSED=0
until curl -sf http://127.0.0.1:8000/api/v1/health > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "      WARNING: AI Engine did not respond within ${MAX_WAIT}s."
        echo "      Express will start anyway — subprocess fallback active."
        break
    fi
    sleep 3
    ELAPSED=$((ELAPSED + 3))
    echo "      Waiting... (${ELAPSED}s elapsed)"
done

if curl -sf http://127.0.0.1:8000/api/v1/health > /dev/null 2>&1; then
    echo "      ✓ AI Engine is online and healthy."
fi

# ── 3. Start Express Backend in foreground ───────────────────
echo "[3/3] Starting Express Backend (Node.js on :${PORT:-3000})..."
echo "═══════════════════════════════════════════════════════════"
exec node server.js
