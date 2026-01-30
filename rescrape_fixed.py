#!/usr/bin/env python3
"""Rescrape with fixed parser and plausibility checks."""

import subprocess
from pathlib import Path

base = Path(__file__).resolve().parent
urls_file = base / "urls.txt"

if not urls_file.exists():
    print(f"❌ {urls_file} not found")
    exit(1)

urls = [line.strip() for line in urls_file.read_text(encoding="utf-8").splitlines() if line.strip()]

if not urls:
    print("❌ No URLs found")
    exit(1)

print(f"Rescraping {len(urls)} pools with FIXED parser...\n")

# Run FIXED scraper (copy fixed version to main location)
import shutil
fixed_scraper = base / "scraper" / "scrape_pools_fixed.py"
main_scraper = base / "scraper" / "scrape_pools.py"

if fixed_scraper.exists():
    print(f"Copying fixed scraper to main location...")
    shutil.copy(fixed_scraper, main_scraper)

result = subprocess.run(
    ["python3", "scraper/scrape_pools.py"] + urls,
    cwd=base
)

if result.returncode != 0:
    print("❌ Scraper failed")
    exit(1)

print("\n" + "="*70)
print("Scraping complete. Running plausibility cleaner...")
print("="*70 + "\n")

result = subprocess.run(["python3", "clean_with_check.py"], cwd=base)

if result.returncode != 0:
    print("❌ Cleaner failed")
    exit(1)

print("\n" + "="*70)
print("✅ All done! Ready to deploy.")
print("="*70)
print("\nNext: git add -A && git commit && git push")
