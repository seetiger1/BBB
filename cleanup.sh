#!/bin/bash
# Cleanup script for BBB repo — removes large files from git history

set -e  # Exit on error

LOG_FILE="/workspaces/BBB/cleanup.log"

echo "=== BBB Repo Cleanup Started ===" | tee "$LOG_FILE"
echo "Date: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

cd /workspaces/BBB
echo "[1] Current directory: $(pwd)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[2] Git status before cleanup:" | tee -a "$LOG_FILE"
git status | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[3] Resetting staging area..." | tee -a "$LOG_FILE"
git reset HEAD 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[4] Removing node_modules from git cache (if exists)..." | tee -a "$LOG_FILE"
git rm --cached -r node_modules 2>&1 | tee -a "$LOG_FILE" || echo "node_modules not in index" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[5] Removing .venv from git cache (if exists)..." | tee -a "$LOG_FILE"
git rm --cached -r .venv 2>&1 | tee -a "$LOG_FILE" || echo ".venv not in index" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[6] Removing __pycache__ from git cache (if exists)..." | tee -a "$LOG_FILE"
git rm --cached -r __pycache__ 2>&1 | tee -a "$LOG_FILE" || echo "__pycache__ not in index" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[7] Removing .next from git cache (if exists)..." | tee -a "$LOG_FILE"
git rm --cached -r .next 2>&1 | tee -a "$LOG_FILE" || echo ".next not in index" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[8] Staging .gitignore..." | tee -a "$LOG_FILE"
git add .gitignore | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[9] Committing .gitignore update..." | tee -a "$LOG_FILE"
git commit -m "chore: update .gitignore to exclude deps, caches, venv" 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[10] Git status after cleanup:" | tee -a "$LOG_FILE"
git status | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[11] Files in git index (first 20):" | tee -a "$LOG_FILE"
git ls-files | head -20 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[12] Performing force-push..." | tee -a "$LOG_FILE"
git push origin main --force-with-lease 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "=== Cleanup Complete ===" | tee -a "$LOG_FILE"
echo "Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"
