#!/usr/bin/env python3
"""Simple scraper for Berliner Bäder pool pages.

Usage:
  python scraper/scrape_pools.py <url1> <url2> ...
  python scraper/scrape_pools.py --file urls.txt

Writes UTF-8 JSON to `data/pools.json`.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "pools.json"
DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

WEEKDAYS = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]


def fetch_page(url: str, timeout: int = 10) -> str:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding
    return resp.text


def extract_text_near_label(soup: BeautifulSoup, label_keywords: List[str]) -> str:
    """Try to find element containing any of the label keywords and return nearby text.

    This is a forgiving approach: if structure changes we still return a reasonable
    text fallback rather than crashing.
    """
    for kw in label_keywords:
        found = soup.find(string=lambda s: s and kw.lower() in s.lower())
        if found:
            parent = found.parent
            # Look for sibling or next elements that might contain hours
            for sib in parent.find_next_siblings(limit=5):
                text = sib.get_text(separator=" ", strip=True)
                if text:
                    return text
            # fallback to parent's text
            return parent.get_text(separator=" ", strip=True)
    # ultimate fallback: whole page text (trimmed)
    return soup.get_text(separator=" ", strip=True)[:1000]


def parse_pool(url: str) -> Dict:
    """Parse pool hours from HTML.
    
    Strategy: Ignore complex table structure, just look for text patterns:
    "WEEKDAY_NAME ... HH:MM - HH:MM Uhr DESCRIPTION"
    
    Extract entries by searching for weekday names followed by times.
    """
    try:
        html = fetch_page(url)
    except Exception as e:
        return {
            "name": "(failed to fetch)",
            "hours": {wd: [] for wd in WEEKDAYS},
            "source_url": url,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }

    soup = BeautifulSoup(html, "html.parser")

    # Extract name
    name = None
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        name = h1.get_text(strip=True)
    if not name and soup.title:
        name = soup.title.get_text(strip=True)
    if not name:
        strong = soup.find("strong")
        if strong:
            name = strong.get_text(strip=True)
    if not name:
        name = url

    # Initialize hours
    hours: Dict[str, List[str]] = {wd: [] for wd in WEEKDAYS}

    # Get all text from page, normalized
    full_text = soup.get_text(separator="\n", strip=True)
    
    # Normalize: reduce excessive whitespace
    full_text = re.sub(r'\n\s*\n+', '\n', full_text)  # remove blank lines
    full_text = re.sub(r'[ \t]+', ' ', full_text)      # normalize spaces

    # Pattern: One or more time entries for a weekday
    # Looking for: "WEEKDAY ... TIME - TIME Uhr DESCRIPTION"
    # Strategy: For each weekday, extract all times that follow it until next weekday
    
    for i, weekday in enumerate(WEEKDAYS):
        # Find all occurrences of this weekday
        lines = full_text.split('\n')
        
        in_weekday_section = False
        weekday_entries = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line contains current weekday
            if weekday.lower() in line.lower():
                in_weekday_section = True
                # Extract times from this line
                times = extract_times_from_line(line, weekday)
                weekday_entries.extend(times)
            
            # Check if we hit the next weekday
            elif in_weekday_section:
                next_wd_found = False
                for other_wd in WEEKDAYS:
                    if other_wd.lower() in line.lower() and other_wd != weekday:
                        next_wd_found = True
                        break
                
                if next_wd_found:
                    in_weekday_section = False
                else:
                    # Still in weekday section, try to extract times
                    times = extract_times_from_line(line, weekday)
                    if times:
                        weekday_entries.extend(times)
        
        # Deduplicate and add to hours
        seen = set()
        for entry in weekday_entries:
            entry_lower = entry.lower()
            if entry_lower not in seen:
                seen.add(entry_lower)
                hours[weekday].append(entry)

    # If still nothing found, fallback to simple pattern search
    if not any(hours.values()):
        fallback = extract_text_near_label(soup, ["Öffnungszeiten", "Öffnungszeit"])[:1000]
        # Try basic extraction from fallback
        for wd in WEEKDAYS:
            pattern = rf'{wd}.*?(\d{{1,2}}:\d{{2}}\s*-\s*\d{{1,2}}:\d{{2}}\s*Uhr\s+[^;]{{0,100}})'
            matches = re.findall(pattern, fallback, re.IGNORECASE | re.DOTALL)
            for match in matches:
                entry = match.strip()
                entry = re.sub(r'\s+', ' ', entry)
                if len(entry) > 10:
                    hours[wd].append(entry)

    return {
        "name": name,
        "hours": hours,
        "source_url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def extract_times_from_line(line: str, expected_weekday: str) -> List[str]:
    """Extract all time entries from a single line."""
    # Pattern: HH:MM - HH:MM Uhr DESCRIPTION
    pattern = re.compile(
        r'(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*[Uu]hr\s+[^;,]*?)(?=\d{1,2}:\d{2}\s*[-–]|;|,|$)',
    )
    
    matches = pattern.findall(line)
    results = []
    
    for match in matches:
        entry = match.strip()
        
        # Remove weekday name if present
        entry = re.sub(rf'^({"|".join(WEEKDAYS)})\s*', '', entry, flags=re.IGNORECASE).strip()
        
        # Normalize whitespace
        entry = re.sub(r'\s+', ' ', entry)
        
        # Limit length
        if len(entry) > 150:
            entry = entry[:150].rsplit(' ', 1)[0]
        
        if len(entry) >= 10:  # must be substantial
            results.append(entry)
    
    return results


def write_json(data: List[Dict]) -> None:
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape pool pages and cache to data/pools.json")
    parser.add_argument("urls", nargs="*", help="Pool detail URLs")
    parser.add_argument("--file", help="File with one URL per line")
    args = parser.parse_args()

    urls: List[str] = list(args.urls or [])
    if args.file:
        p = Path(args.file)
        if p.exists():
            urls.extend([line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()])

    if not urls:
        print("No URLs provided. Exiting.")
        return

    results = []
    for url in urls:
        print(f"Fetching {url}...")
        try:
            res = parse_pool(url)
            results.append(res)
        except Exception as e:
            # keep going even if one page fails
            results.append({
                "name": "(error)",
                "hours": {},
                "source_url": url,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
            })

    write_json(results)
    print(f"Wrote {len(results)} pools to {DATA_PATH}")


if __name__ == "__main__":
    main()
