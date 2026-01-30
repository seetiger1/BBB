#!/usr/bin/env python3
import subprocess
import sys
import os

os.chdir('/workspaces/BBB')

print("🔄 Rescraping pools with improved parser...")
result = subprocess.run([sys.executable, 'scraper/scrape_pools.py', '--file', 'urls.txt'], check=True)

print("✅ Validating JSON...")
result = subprocess.run([sys.executable, '-m', 'json.tool', 'data/pools.json'], 
                       stdout=subprocess.DEVNULL, check=True)

print("📤 Pushing to GitHub...")
subprocess.run(['git', 'add', '-A'], check=True)
subprocess.run(['git', 'commit', '-m', 'fix: improve scraper to extract only time patterns, remove page clutter'], check=True)
subprocess.run(['git', 'push'], check=True)

print("✨ Done! Vercel will redeploy in ~2-3 minutes...")
