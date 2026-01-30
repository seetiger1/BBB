#!/bin/bash
# Fix Vercel deployment issues

set -e

LOG_FILE="/workspaces/BBB/vercel_fix.log"

echo "=== Vercel Deployment Fix ===" | tee "$LOG_FILE"
echo "Date: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

cd /workspaces/BBB

echo "[1] Status:" | tee -a "$LOG_FILE"
git status | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[2] Adding all changes..." | tee -a "$LOG_FILE"
git add -A | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[3] Committing..." | tee -a "$LOG_FILE"
git commit -m "fix: update API structure for Vercel compatibility (use Next.js API routes)" 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[4] Pushing..." | tee -a "$LOG_FILE"
git push 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[5] Files created/updated:" | tee -a "$LOG_FILE"
echo "  - api/index.py (backup, can remove)" | tee -a "$LOG_FILE"
echo "  - app/api/pools/route.ts (Next.js API route - replaces FastAPI)" | tee -a "$LOG_FILE"
echo "  - next.config.js (Next.js config)" | tee -a "$LOG_FILE"
echo "  - vercel.json (simplified for Vercel)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "=== Ready to redeploy on Vercel ===" | tee -a "$LOG_FILE"
