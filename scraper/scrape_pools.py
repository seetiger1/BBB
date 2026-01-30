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
    """Parse a single pool page with STRUCTURAL table parsing.
    
    Key improvement: Uses column-based approach instead of row scanning.
    Each <table> column = one weekday. Multiple entries per day separated by <br> or newlines.
    This guarantees NO mixing of weekday data.
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

    # Pattern to extract time entries: HH:MM - HH:MM Uhr DESCRIPTION
    time_pattern = re.compile(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*Uhr')

    # STRUCTURAL APPROACH: Find table and use column indexing
    tables = soup.find_all('table')
    
    for table in tables:
        # Get header row to map columns to weekdays
        header_row = table.find('thead')
        if not header_row:
            header_row = table.find('tr')
        
        if not header_row:
            continue
        
        # Extract header cells (should contain weekday names)
        header_cells = header_row.find_all(['th', 'td'])
        if not header_cells:
            continue
        
        # Map column index → weekday
        column_to_day = {}
        for col_idx, header_cell in enumerate(header_cells):
            header_text = header_cell.get_text(strip=True).lower()
            for weekday in WEEKDAYS:
                if weekday.lower() in header_text:
                    column_to_day[col_idx] = weekday
                    break
        
        if not column_to_day:
            # No valid weekday headers found, try next table
            continue
        
        # Now process all rows in tbody (skip thead)
        tbody = table.find('tbody')
        if tbody:
            data_rows = tbody.find_all('tr')
        else:
            # Fallback: use all rows after header
            all_rows = table.find_all('tr')
            data_rows = all_rows[1:] if len(all_rows) > 1 else []
        
        # Extract time entries from each cell
        for row in data_rows:
            cells = row.find_all(['td', 'th'])
            
            for col_idx, cell in enumerate(cells):
                if col_idx not in column_to_day:
                    continue
                
                weekday = column_to_day[col_idx]
                
                # Get cell text, splitting by <br> to handle multiple entries
                cell_lines = []
                for line in cell.stripped_strings:
                    line = line.strip()
                    if line:
                        cell_lines.append(line)
                
                # Also check for explicit <br> separation
                br_chunks = []
                for br in cell.find_all('br'):
                    # Get text before br
                    prev_text = ""
                    elem = br.previous_sibling
                    while elem:
                        if isinstance(elem, str):
                            prev_text = elem.strip() + prev_text
                        elem = elem.previous_sibling
                    if prev_text:
                        br_chunks.append(prev_text)
                
                # Combine approaches
                all_text = " ".join(cell_lines)
                
                # Split by newlines or multiple spaces (indicating separate entries)
                entries_raw = re.split(r'[\n;]|\s{2,}', all_text)
                
                # Process each potential entry
                for entry_raw in entries_raw:
                    entry = entry_raw.strip()
                    if not entry:
                        continue
                    
                    # Must contain a time pattern
                    if not time_pattern.search(entry):
                        continue
                    
                    # Clean entry
                    entry = re.sub(r'\s+', ' ', entry).strip()
                    
                    # Remove weekday name if accidentally included
                    entry = re.sub(rf'^({"|".join(WEEKDAYS)})\s*', '', entry, flags=re.IGNORECASE).strip()
                    
                    # Limit length but keep at word boundary
                    if len(entry) > 150:
                        entry = entry[:150].rsplit(' ', 1)[0]
                    
                    # Add if valid and new
                    if len(entry) >= 10:
                        entry_lower = entry.lower()
                        if not any(e.lower() == entry_lower for e in hours[weekday]):
                            hours[weekday].append(entry)
    
    # Fallback if no table found
    if not any(hours.values()):
        fallback = extract_text_near_label(soup, ["Öffnungszeiten", "Öffnungszeit", "Öffnen"])[:500]
        if fallback:
            for wd in WEEKDAYS:
                hours[wd] = [fallback[:150]]

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
