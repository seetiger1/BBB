#!/bin/bash
# Remove vercel.json entirely and force fresh Vercel detection

set -e

LOG_FILE="/workspaces/BBB/nuclear_option.log"

echo "=== Nuclear Option: Remove vercel.json ===" | tee "$LOG_FILE"
echo "Date: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

cd /workspaces/BBB

echo "[1] Removing vercel.json (let Vercel auto-detect)..." | tee -a "$LOG_FILE"
git rm vercel.json 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[2] Committing..." | tee -a "$LOG_FILE"
git commit -m "chore: remove vercel.json (let Vercel auto-detect Next.js)" 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[3] Pushing..." | tee -a "$LOG_FILE"
git push 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[4] Git log:" | tee -a "$LOG_FILE"
git log --oneline | head -3 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "=== Done ===" | tee -a "$LOG_FILE"
echo "Now on Vercel:" | tee -a "$LOG_FILE"
echo "1. Settings → Advanced → Clear Build Cache" | tee -a "$LOG_FILE"
echo "2. Deployments → Redeploy" | tee -a "$LOG_FILE"
