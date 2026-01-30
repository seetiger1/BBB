#!/bin/bash
# Commit and push all changes

set -e

LOG_FILE="/workspaces/BBB/final_push.log"

echo "=== Final Commit & Push ===" | tee "$LOG_FILE"
echo "Date: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

cd /workspaces/BBB

echo "[1] Git status:" | tee -a "$LOG_FILE"
git status | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[2] Adding all changes..." | tee -a "$LOG_FILE"
git add -A | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[3] Committing..." | tee -a "$LOG_FILE"
git commit -m "feat: improve UI, add GitHub Actions, prepare Vercel deployment" 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[4] Pushing to GitHub..." | tee -a "$LOG_FILE"
git push 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[5] Final log:" | tee -a "$LOG_FILE"
git log --oneline | head -5 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "=== Complete ===" | tee -a "$LOG_FILE"
