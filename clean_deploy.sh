#!/bin/bash
# Clean build artifacts and prepare for Vercel

set -e

LOG_FILE="/workspaces/BBB/clean_deploy.log"

echo "=== Cleaning Build Artifacts ===" | tee "$LOG_FILE"
echo "Date: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

cd /workspaces/BBB

echo "[1] Removing .next directory..." | tee -a "$LOG_FILE"
rm -rf .next 2>&1 | tee -a "$LOG_FILE" || echo "Already clean" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[2] Removing .vercel directory..." | tee -a "$LOG_FILE"
rm -rf .vercel 2>&1 | tee -a "$LOG_FILE" || echo "Already clean" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[3] Status:" | tee -a "$LOG_FILE"
git status | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[4] Committing .gitignore updates..." | tee -a "$LOG_FILE"
git add .gitignore
git commit -m "chore: improve .gitignore (add .vercel, log files)" 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[5] Pushing..." | tee -a "$LOG_FILE"
git push 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "=== Ready for Clean Vercel Deploy ===" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Next steps:" | tee -a "$LOG_FILE"
echo "1. Go to Vercel Dashboard" | tee -a "$LOG_FILE"
echo "2. Go to your BBB project → Settings → Advanced → Danger Zone" | tee -a "$LOG_FILE"
echo "3. Click 'Clear Build Cache'" | tee -a "$LOG_FILE"
echo "4. Click 'Redeploy' or wait for auto-redeploy (1 min)" | tee -a "$LOG_FILE"
