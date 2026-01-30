#!/bin/bash
# Quick fix and redeploy

set -e
cd /workspaces/BBB

echo "Committing vercel.json fix..."
git add vercel.json
git commit -m "fix: simplify vercel.json for auto-detection"
git push

echo "✓ Done. Now redeploy on Vercel."
