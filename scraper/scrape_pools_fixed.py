#!/usr/bin/env python3
"""Scraper for Berliner Bäder pool pages - FIXED VERSION."""
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
    """Find element containing keywords and return nearby text."""
    for kw in label_keywords:
        found = soup.find(string=lambda s: s and kw.lower() in s.lower())
        if found:
            parent = found.parent
            for sib in parent.find_next_siblings(limit=5):
                text = sib.get_text(separator=" ", strip=True)
                if text:
                    return text
            return parent.get_text(separator=" ", strip=True)
    return soup.get_text(separator=" ", strip=True)[:1000]


def parse_pool(url: str) -> Dict:
    """Parse pool hours from website using aggressive text extraction."""
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

    hours: Dict[str, List[str]] = {wd: [] for wd in WEEKDAYS}

    # Get ALL text and normalize
    full_text = soup.get_text(separator=" ", strip=True)
    full_text = re.sub(r'\s+', ' ', full_text)
    
    # Find opening hours section
    hours_idx = full_text.lower().find('öffnung')
    if hours_idx >= 0:
        hours_text = full_text[max(0, hours_idx - 100):min(len(full_text), hours_idx + 5000)]
    else:
        hours_text = full_text
    
    # Extract times for each weekday
    for weekday_idx, weekday in enumerate(WEEKDAYS):
        wd_pattern = re.compile(rf'\b{weekday}\b', re.IGNORECASE)
        match = wd_pattern.search(hours_text)
        
        if not match:
            continue
        
        # Find where this weekday starts
        start_pos = match.start()
        
        # Find the next weekday
        end_pos = len(hours_text)
        for future_wd in WEEKDAYS[weekday_idx + 1:]:
            future_pattern = re.compile(rf'\b{future_wd}\b', re.IGNORECASE)
            future_match = future_pattern.search(hours_text, start_pos + len(weekday))
            if future_match:
                end_pos = future_match.start()
                break
        
        # Extract the chunk for this weekday
        chunk = hours_text[start_pos:end_pos]
        
        # Check if this section contains "Geschlossen"
        if 'geschlossen' in chunk.lower():
            hours[weekday].append("Geschlossen")
            continue
        
        # Find all times in chunk: HH:MM - HH:MM followed by description
        time_pattern = re.compile(
            r'(\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}(?:\s+[Uu]hr)?(?:\s+[^;,\n]{0,80})?)',
            re.IGNORECASE
        )
        
        matches = time_pattern.findall(chunk)
        seen = set()
        
        for match in matches:
            entry = match.strip()
            
            # Remove leading weekday name
            entry = re.sub(rf'^{weekday}\s*', '', entry, flags=re.IGNORECASE).strip()
            
            # Normalize spaces
            entry = re.sub(r'\s+', ' ', entry)
            
            # Ensure "Uhr" is present
            if 'uhr' not in entry.lower():
                entry = entry.rstrip('.,:;') + ' Uhr'
            
            # Clean trailing junk
            entry = re.sub(r'[,;\.]+\s*$', '', entry)
            
            # Limit length at word boundary
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
        except Exception as e:
            results.append({
                "name": "(error)",
                "hours": {wd: [] for wd in WEEKDAYS},
                "source_url": url,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
            })

    write_json(results)
    print(f"✅ Wrote {len(results)} pools to {DATA_PATH}")


if __name__ == "__main__":
    main()
