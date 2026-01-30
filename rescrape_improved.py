#!/usr/bin/env python3
"""
Rescrape all pools with improved parser.
This script fetches all pools fresh and applies the new structured parsing.
"""

import sys
import subprocess
from pathlib import Path

# Get list of URLs
urls_file = Path(__file__).resolve().parent / "urls.txt"

if not urls_file.exists():
    print(f"Error: {urls_file} not found")
    sys.exit(1)

urls = [line.strip() for line in urls_file.read_text(encoding="utf-8").splitlines() if line.strip()]

if not urls:
    print("No URLs found in urls.txt")
    sys.exit(1)

print(f"Rescraping {len(urls)} pools with improved parser...\n")

# Run scraper
cmd = ["python3", "scraper/scrape_pools.py"] + urls
result = subprocess.run(cmd, cwd=Path(__file__).resolve().parent)

if result.returncode != 0:
    print(f"Scraper failed with exit code {result.returncode}")
    sys.exit(1)

print("\n" + "="*60)
print("Scraping complete. Now cleaning data...")
print("="*60 + "\n")

# Run cleaner
cmd = ["python3", "clean_data_new.py"]
result = subprocess.run(cmd, cwd=Path(__file__).resolve().parent)

if result.returncode != 0:
    print(f"Cleaner failed with exit code {result.returncode}")
    sys.exit(1)

print("\n✅ All done! Data is clean and ready.")
print("\nNext: git add -A && git commit -m 'fix: improve parser with structured HTML selection' && git push")
