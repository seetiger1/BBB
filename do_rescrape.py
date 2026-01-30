#!/usr/bin/env python3
"""
Rescrape with improved structural parser and strict cleaner.
"""

import subprocess
from pathlib import Path

base_path = Path(__file__).resolve().parent
urls_file = base_path / "urls.txt"

if not urls_file.exists():
    print(f"Error: {urls_file} not found")
    exit(1)

urls = [line.strip() for line in urls_file.read_text(encoding="utf-8").splitlines() if line.strip()]

if not urls:
    print("No URLs found")
    exit(1)

print(f"Rescraping {len(urls)} pools with structural parser...\n")

# Run scraper
result = subprocess.run(
    ["python3", "scraper/scrape_pools.py"] + urls,
    cwd=base_path
)

if result.returncode != 0:
    print("Scraper failed")
    exit(1)

print("\n" + "="*70)
print("Scraping complete. Running strict cleaner...")
print("="*70 + "\n")

# Run cleaner
result = subprocess.run(["python3", "clean_strict.py"], cwd=base_path)

if result.returncode != 0:
    print("Cleaner failed")
    exit(1)

print("\n" + "="*70)
print("✅ All done! Data is clean and ready to deploy.")
print("="*70)
print("\nNext step: git add -A && git commit -m \"fix: structural table parser\" && git push")
