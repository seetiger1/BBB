#!/bin/bash
# Comprehensive local tests before Vercel deploy

set -e

LOG_FILE="/workspaces/BBB/local_tests.log"

echo "=== Local Tests for Vercel Readiness ===" | tee "$LOG_FILE"
echo "Date: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

cd /workspaces/BBB

# Test 1: Files exist
echo "[TEST 1] Required files exist:" | tee -a "$LOG_FILE"
FILES=("package.json" "data/pools.json" "app/page.tsx" "app/api/pools/route.ts" "next.config.js")
for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "  ✓ $file" | tee -a "$LOG_FILE"
  else
    echo "  ✗ MISSING: $file" | tee -a "$LOG_FILE"
  fi
done
echo "" | tee -a "$LOG_FILE"

# Test 2: data/pools.json is valid JSON
echo "[TEST 2] data/pools.json is valid JSON:" | tee -a "$LOG_FILE"
if python3 -m json.tool data/pools.json > /dev/null 2>&1; then
  POOL_COUNT=$(python3 -c "import json; print(len(json.load(open('data/pools.json'))))")
  echo "  ✓ Valid JSON with $POOL_COUNT pools" | tee -a "$LOG_FILE"
else
  echo "  ✗ Invalid JSON in data/pools.json" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# Test 3: Check vercel.json
echo "[TEST 3] vercel.json content:" | tee -a "$LOG_FILE"
cat vercel.json | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 4: Check package.json has Next.js
echo "[TEST 4] Next.js in package.json:" | tee -a "$LOG_FILE"
if grep -q '"next"' package.json; then
  NEXT_VERSION=$(grep '"next"' package.json | head -1)
  echo "  ✓ Found: $NEXT_VERSION" | tee -a "$LOG_FILE"
else
  echo "  ✗ Next.js not found in package.json" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# Test 5: Check API route exists and is valid TypeScript
echo "[TEST 5] API route (app/api/pools/route.ts):" | tee -a "$LOG_FILE"
if [ -f "app/api/pools/route.ts" ]; then
  echo "  ✓ File exists" | tee -a "$LOG_FILE"
  if grep -q "GET\|export async function GET" app/api/pools/route.ts; then
    echo "  ✓ Exports GET function" | tee -a "$LOG_FILE"
  else
    echo "  ✗ Missing GET export" | tee -a "$LOG_FILE"
  fi
else
  echo "  ✗ File missing" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# Test 6: Check next.config.js exists
echo "[TEST 6] next.config.js exists:" | tee -a "$LOG_FILE"
if [ -f "next.config.js" ]; then
  echo "  ✓ File exists" | tee -a "$LOG_FILE"
  head -3 next.config.js | tee -a "$LOG_FILE"
else
  echo "  ✗ File missing (optional but recommended)" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# Test 7: Node modules status
echo "[TEST 7] node_modules status:" | tee -a "$LOG_FILE"
if [ -d "node_modules" ]; then
  MODULE_COUNT=$(find node_modules -type d -maxdepth 1 | wc -l)
  echo "  ✓ node_modules exists ($MODULE_COUNT directories)" | tee -a "$LOG_FILE"
else
  echo "  ⚠ node_modules missing (will be installed during build)" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# Test 8: Try to build locally (if node_modules exist)
if [ -d "node_modules" ]; then
  echo "[TEST 8] Running 'npm run build' locally:" | tee -a "$LOG_FILE"
  if npm run build 2>&1 | tee -a "$LOG_FILE"; then
    echo "  ✓ Build successful!" | tee -a "$LOG_FILE"
    if [ -d ".next" ]; then
      echo "  ✓ .next output directory created" | tee -a "$LOG_FILE"
    fi
  else
    echo "  ✗ Build failed" | tee -a "$LOG_FILE"
  fi
else
  echo "[TEST 8] Skipping build test (install node_modules first)" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

echo "=== Test Summary ===" | tee -a "$LOG_FILE"
echo "Check the log above for any ✗ marks." | tee -a "$LOG_FILE"
echo "Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"
