#!/bin/bash
# Start script for frontend dev — with full logging

set -e

LOG_FILE="/workspaces/BBB/frontend_dev.log"

echo "=== Frontend Dev Start ===" | tee "$LOG_FILE"
echo "Date: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

cd /workspaces/BBB

echo "[1] Clearing npm cache..." | tee -a "$LOG_FILE"
npm cache clean --force 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[2] Removing node_modules & package-lock (fresh install)..." | tee -a "$LOG_FILE"
rm -rf node_modules package-lock.json 2>&1 | tee -a "$LOG_FILE" || true
echo "" | tee -a "$LOG_FILE"

echo "[3] Running npm install..." | tee -a "$LOG_FILE"
npm install 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[4] Checking node_modules installed successfully..." | tee -a "$LOG_FILE"
ls -la node_modules | head -20 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[5] Starting dev server with NEXT_PUBLIC_API_BASE..." | tee -a "$LOG_FILE"
echo "Frontend will run on http://localhost:3000" | tee -a "$LOG_FILE"
echo "API should be running on http://localhost:8000" | tee -a "$LOG_FILE"
echo "Press Ctrl+C to stop." | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Start the dev server (foreground, will keep running until Ctrl+C)
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev 2>&1 | tee -a "$LOG_FILE"
