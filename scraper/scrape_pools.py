#!/usr/bin/env python3
"""Scraper for Berliner Bäder pool pages - FIXED VERSION with improved parsing."""
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


def extract_hours_from_table(soup: BeautifulSoup) -> Dict[str, List[str]]:
    """Extract opening hours from HTML table structure."""
    hours: Dict[str, List[str]] = {wd: [] for wd in WEEKDAYS}
    
    # Find all tables
    tables = soup.find_all("table")
    if not tables:
        return hours
    
    for table in tables:
        # Get all rows
        rows = table.find_all("tr")
        if not rows:
            continue
        
        # Try to find header row with weekday names
        header_row = None
        header_idx = -1
        
        for idx, row in enumerate(rows):
            cells = row.find_all(["th", "td"])
            row_text = " ".join([cell.get_text(strip=True) for cell in cells])
            
            # Check if this row contains weekday names
            weekday_count = sum(1 for wd in WEEKDAYS if wd.lower() in row_text.lower())
            if weekday_count >= 5:  # At least 5 weekdays found
                header_row = row
                header_idx = idx
                break
        
        if header_row is None:
            continue
        
        # Find column indices for each weekday
        header_cells = header_row.find_all(["th", "td"])
        weekday_cols: Dict[str, int] = {}
        
        for col_idx, cell in enumerate(header_cells):
            cell_text = cell.get_text(strip=True).lower()
            for wd in WEEKDAYS:
                if wd.lower() in cell_text or cell_text.startswith(wd.lower()[:2]):
                    weekday_cols[wd] = col_idx
                    break
        
        if not weekday_cols:
            continue
        
        # Extract times from data rows
        for row_idx in range(header_idx + 1, len(rows)):
            row = rows[row_idx]
            cells = row.find_all(["td", "th"])
            
            if not cells:
                continue
            
            for weekday, col_idx in weekday_cols.items():
                if col_idx >= len(cells):
                    continue
                
                cell = cells[col_idx]
                cell_text = cell.get_text(separator="|", strip=True)
                
                # Split by <br> or pipe separator
                entries = [e.strip() for e in cell_text.split("|") if e.strip()]
                
                for entry in entries:
                    entry = entry.strip()
                    
                    # Check for "Geschlossen"
                    if entry.lower() == "geschlossen":
                        if not hours[weekday]:  # Only add if no other entries
                            hours[weekday].append("Geschlossen")
                        continue
                    
                    # Clean entry: remove extra whitespace
                    entry = re.sub(r'\s+', ' ', entry)
                    
                    # Validate: must contain time pattern HH:MM
                    if not re.search(r'\d{1,2}:\d{2}', entry):
                        continue
                    
                    # Ensure "Uhr" is present
                    if "uhr" not in entry.lower():
                        entry = entry + " Uhr"
                    
                    # Limit length to 150 chars at word boundary
                    if len(entry) > 150:
                        words = entry.split()
                        truncated = []
                        length = 0
                        for word in words:
                            if length + len(word) + 1 > 150:
                                break
                            truncated.append(word)
                            length += len(word) + 1
                        entry = " ".join(truncated)
                    
                    # Deduplicate
                    entry_lower = entry.lower()
                    if entry not in hours[weekday]:
                        hours[weekday].append(entry)
    
    return hours


def extract_hours_from_text_fallback(full_text: str) -> Dict[str, List[str]]:
    """Fallback: Extract opening hours from plain text using improved regex logic."""
    hours: Dict[str, List[str]] = {wd: [] for wd in WEEKDAYS}
    
    # Normalize whitespace
    full_text = re.sub(r'\s+', ' ', full_text)
    
    # Find opening hours section
    hours_idx = full_text.lower().find('öffnung')
    if hours_idx < 0:
        hours_idx = 0
    else:
        hours_idx = max(0, hours_idx - 100)
    
    hours_text = full_text[hours_idx:min(len(full_text), hours_idx + 8000)]
    
    # For each weekday, extract only until the NEXT weekday or end marker
    for weekday_idx, weekday in enumerate(WEEKDAYS):
        wd_pattern = re.compile(rf'\b{weekday}\b', re.IGNORECASE)
        match = wd_pattern.search(hours_text)
        
        if not match:
            continue
        
        start_pos = match.start()
        
        # Limit lookahead to prevent grabbing excessive text at end of file
        end_pos = min(len(hours_text), start_pos + 400)
        
        # Look for the next weekday to mark the boundary
        if weekday_idx + 1 < len(WEEKDAYS):
            next_wd = WEEKDAYS[weekday_idx + 1]
            next_pattern = re.compile(rf'\b{next_wd}\b', re.IGNORECASE)
            next_match = next_pattern.search(hours_text, start_pos + len(weekday))
            if next_match and next_match.start() < end_pos:
                end_pos = next_match.start()
        else:
            # For Sunday, look for Monday to detect if a new block starts
            next_wd = WEEKDAYS[0]
            next_pattern = re.compile(rf'\b{next_wd}\b', re.IGNORECASE)
            next_match = next_pattern.search(hours_text, start_pos + len(weekday))
            if next_match and next_match.start() < end_pos:
                end_pos = next_match.start()

        # Extract chunk for this weekday only
        chunk = hours_text[start_pos:end_pos]
        
        # Check if closed
        if 'geschlossen' in chunk.lower():
            hours[weekday].append("Geschlossen")
            continue
        
        # Extract time patterns: HH:MM - HH:MM followed by description (max 70 chars)
        time_pattern = re.compile(
            r'(\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}(?:\s+[Uu]hr)?(?:\s+[^;\n]{0,70})?)',
            re.IGNORECASE
        )
        
        matches = time_pattern.findall(chunk)
        seen = set()
        
        for match in matches:
            entry = match.strip()
            
            # Remove leading weekday name
            entry = re.sub(rf'^\s*{weekday}\s*', '', entry, flags=re.IGNORECASE).strip()
            
            # Normalize spaces
            entry = re.sub(r'\s+', ' ', entry)
            
            # Ensure "Uhr" is present
            if 'uhr' not in entry.lower():
                entry = entry.rstrip('.,:;') + ' Uhr'
            
            # Clean trailing punctuation
            entry = re.sub(r'[,;\.]+\s*$', '', entry)
            
            # Limit length
            if len(entry) > 150:
                words = entry.split()
                truncated = []
                length = 0
                for word in words:
                    if length + len(word) + 1 > 150:
                        break
                    truncated.append(word)
                    length += len(word) + 1
                entry = ' '.join(truncated)
            
            # Validate and deduplicate
            if len(entry) >= 10 and re.search(r'\d{1,2}:\d{2}', entry):
                entry_lower = entry.lower()
                if entry_lower not in seen:
                    seen.add(entry_lower)
                    hours[weekday].append(entry)
    
    return hours


def parse_pool(url: str) -> Dict:
    """Parse pool hours from website using table structure and fallback text extraction."""
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
    if h1:
        name = h1.get_text(strip=True)
    if not name:
        name = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]

    # Try table-based extraction first
    hours = extract_hours_from_table(soup)
    
    # If no hours found, use text-based fallback
    if not any(hours.values()):
        full_text = soup.get_text(separator=" ", strip=True)
        hours = extract_hours_from_text_fallback(full_text)

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
    parser = argparse.ArgumentParser(description="Scrape pool pages")
    parser.add_argument("urls", nargs="*", help="Pool URLs")
    parser.add_argument("--file", help="File with URLs")
    args = parser.parse_args()

    urls: List[str] = list(args.urls or [])
    if args.file:
        p = Path(args.file)
        if p.exists():
            urls.extend([line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()])

    if not urls:
        print("No URLs provided.")
        return

    results = []
    for url in urls:
        print(f"Fetching {url}...")
        try:
            res = parse_pool(url)
            results.append(res)
            print(f"  ✓ {res['name']}")
            for wd, times in res['hours'].items():
                if times:
                    print(f"    {wd}: {len(times)} entry(ies)")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                "name": "(error)",
                "hours": {wd: [] for wd in WEEKDAYS},
                "source_url": url,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
            })

    write_json(results)
    print(f"\n✅ Wrote {len(results)} pools to {DATA_PATH}")


if __name__ == "__main__":
    main()
