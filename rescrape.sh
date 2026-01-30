#!/bin/bash
# Rescrape with improved parser + commit + push

set -e

LOG_FILE="/workspaces/BBB/rescrape.log"

echo "=== Rescraping with Improved Parser ===" | tee "$LOG_FILE"
echo "Date: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

cd /workspaces/BBB

# Activate venv
source .venv/bin/activate

echo "[1] Running scraper..." | tee -a "$LOG_FILE"
python scraper/scrape_pools.py --file urls.txt 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[2] Validating JSON..." | tee -a "$LOG_FILE"
python -m json.tool data/pools.json > /dev/null 2>&1 && echo "✓ Valid JSON" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[3] Sample data (first pool, Montag):" | tee -a "$LOG_FILE"
python -c "import json; d=json.load(open('data/pools.json')); print(json.dumps(d[0] if d else {}, indent=2, ensure_ascii=False))" | head -20 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[4] Committing changes..." | tee -a "$LOG_FILE"
git add -A
git commit -m "feat: improve scraper to collect ALL opening times per day, update UI to show all weekdays" 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[5] Pushing to GitHub..." | tee -a "$LOG_FILE"
git push 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "=== Done ===" | tee -a "$LOG_FILE"
echo "Vercel will auto-redeploy. Check your site in 2-3 minutes!" | tee -a "$LOG_FILE"
