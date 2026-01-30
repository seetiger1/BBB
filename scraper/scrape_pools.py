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
    """Parse a single pool page and return a dict with required fields.

    Uses structural HTML parsing: looks for opening hours tables with proper selectors.
    Each weekday can have multiple entries (different activity types or times).
    
    Expected format: Weekday | Time range | Activity type
    E.g. "Montag | 06:30 - 08:00 Uhr | öffentl. Schwimmen"
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

    # Name: prefer <h1>, then <title>, then first strong tag
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

    # Hours: collect ALL entries per weekday
    hours: Dict[str, List[str]] = {wd: [] for wd in WEEKDAYS}

    # Pattern to match complete time entries: HH:MM - HH:MM Uhr DESCRIPTION
    time_entry_pattern = re.compile(
        r'(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*Uhr\s+.{1,200}?)(?=\d{1,2}:\d{2}\s*-|\s*(?:Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)|$)',
        re.IGNORECASE
    )

    # Strategy 1: Look for <table> structures with opening hours
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        if not rows:
            continue
        
        current_weekday = None
        
        for row in rows:
            row_text = row.get_text(separator=" ", strip=True)
            if not row_text:
                continue
            
            # Check if row contains a weekday name
            for wd in WEEKDAYS:
                if wd.lower() in row_text.lower():
                    current_weekday = wd
                    # Extract all time entries from this row
                    cells = row.find_all(['td', 'th'])
                    for cell in cells:
                        cell_text = cell.get_text(separator=" ", strip=True)
                        # Look for time patterns in cell
                        matches = time_entry_pattern.findall(cell_text)
                        for match in matches:
                            entry = match.strip()
                            # Remove weekday name if present at start
                            entry = re.sub(rf'^({"|".join(WEEKDAYS)})\s*', '', entry, flags=re.IGNORECASE).strip()
                            # Clean up extra whitespace
                            entry = re.sub(r'\s+', ' ', entry).strip()
                            # Add if valid (has time pattern and not too short)
                            if len(entry) > 10 and re.search(r'\d{1,2}:\d{2}', entry):
                                hours[current_weekday].append(entry)
                    break

    # Strategy 2: If table parsing didn't work, look for structured divs/lists with class hints
    if not any(hours.values()):
        # Look for elements with day/time related classes
        for elem in soup.find_all(['div', 'li', 'p']):
            elem_text = elem.get_text(separator=" ", strip=True)
            if not elem_text or len(elem_text) < 10:
                continue
            
            # Check if element might contain hours (has time pattern)
            if not re.search(r'\d{1,2}:\d{2}', elem_text):
                continue
            
            # For each weekday, look for entries
            for wd in WEEKDAYS:
                if wd.lower() in elem_text.lower():
                    # Extract everything after the weekday name
                    idx = elem_text.lower().find(wd.lower())
                    if idx >= 0:
                        day_content = elem_text[idx + len(wd):]
                        # Extract time entries
                        entries = time_entry_pattern.findall(day_content)
                        for entry in entries:
                            entry = entry.strip()
                            entry = re.sub(r'\s+', ' ', entry).strip()
                            # Limit length to ~120 chars
                            if len(entry) > 120:
                                entry = entry[:120].rsplit(' ', 1)[0]
                            if len(entry) > 10 and re.search(r'\d{1,2}:\d{2}', entry):
                                if entry not in hours[wd]:  # avoid duplicates
                                    hours[wd].append(entry)

    # Strategy 3: Fallback - if still nothing found
    if not any(hours.values()):
        fallback = extract_text_near_label(soup, ["Öffnungszeiten", "Öffnungszeit", "Öffnen"])[:500]
        if fallback:
            # Try to parse fallback text for weekdays
            for wd in WEEKDAYS:
                if wd.lower() in fallback.lower():
                    idx = fallback.lower().find(wd.lower())
                    content = fallback[idx:min(idx + 200, len(fallback))]
                    entries = time_entry_pattern.findall(content)
                    for entry in entries:
                        entry = entry.strip()
                        if len(entry) > 10:
                            hours[wd].append(entry)

    # Post-process: deduplicate per day
    for wd in hours:
        seen = set()
        unique_entries = []
        for entry in hours[wd]:
            entry_key = entry.lower()
            if entry_key not in seen:
                seen.add(entry_key)
                unique_entries.append(entry)
        hours[wd] = unique_entries

    return {
        "name": name,
        "hours": hours,
        "source_url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


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
