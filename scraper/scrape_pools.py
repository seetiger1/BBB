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

    The parser is defensive: it attempts several heuristics and never raises
    on missing expected nodes — instead it keeps readable fallbacks.
    """
    try:
        html = fetch_page(url)
    except Exception as e:
        return {
            "name": "(failed to fetch)",
            "hours": {},
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

    # Hours: try to find table rows mentioning weekdays, otherwise look for 'Öffnungszeiten'
    hours: Dict[str, str] = {}

    # Search for table rows or list items that contain weekday names
    found_any = False
    for tr in soup.find_all(["tr", "li", "p", "div"]):
        text = tr.get_text(separator=" ", strip=True)
        if not text:
            continue
        for wd in WEEKDAYS:
            if wd.lower() in text.lower():
                # try to split by ':' or '–' or '-' to get times
                hours[wd] = text
                found_any = True
    if not found_any:
        # fallback: find near 'Öffnungszeiten' label
        fallback = extract_text_near_label(soup, ["Öffnungszeiten", "Öffnungszeit", "Öffnen"])[:2000]
        # assign same fallback to all weekdays to keep structure predictable
        for wd in WEEKDAYS:
            hours[wd] = fallback

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
