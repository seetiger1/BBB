#!/bin/bash
# Aggressive cleanup: remove node_modules completely from git history using git filter-branch

set -e

LOG_FILE="/workspaces/BBB/cleanup_aggressive.log"

echo "=== Aggressive Git History Cleanup ===" | tee "$LOG_FILE"
echo "Date: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

cd /workspaces/BBB

echo "[1] Showing commits before cleanup:" | tee -a "$LOG_FILE"
git log --oneline --graph | head -10 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[2] Removing node_modules from ALL commits using filter-branch..." | tee -a "$LOG_FILE"
git filter-branch --tree-filter 'rm -rf node_modules' --prune-empty -f HEAD 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[3] Removing .next from ALL commits..." | tee -a "$LOG_FILE"
git filter-branch --tree-filter 'rm -rf .next' --prune-empty -f HEAD 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[4] Force-removing __pycache__ from index (if any):" | tee -a "$LOG_FILE"
git rm --cached -r __pycache__ 2>/dev/null || echo "No __pycache__ to remove" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[5] Git status after aggressive cleanup:" | tee -a "$LOG_FILE"
git status | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[6] Showing commits after cleanup:" | tee -a "$LOG_FILE"
git log --oneline --graph | head -10 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[7] Force-pushing (--force-with-lease)..." | tee -a "$LOG_FILE"
git push origin main --force-with-lease 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "=== Aggressive Cleanup Complete ===" | tee -a "$LOG_FILE"
