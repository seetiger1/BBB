#!/usr/bin/env python3
"""Clean and normalize pool opening hours data with improved logic."""

import json
import re
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "data" / "pools.json"

WEEKDAYS = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]


def clean_entry(entry: str) -> str:
    """Normalize a single time entry."""
    if not entry or not isinstance(entry, str):
        return ""
    
    # Remove leading/trailing weekday names
    entry = re.sub(rf'^({"|".join(WEEKDAYS)})\s*', '', entry, flags=re.IGNORECASE).strip()
    
    # Normalize whitespace (tabs, newlines, multiple spaces)
    entry = re.sub(r'[\n\t\r]+', ' ', entry)
    entry = re.sub(r'\s+', ' ', entry).strip()
    
    # Normalize time separator (- or –)
    entry = re.sub(r'\s*[–—-]\s*', ' - ', entry)
    
    # Ensure "Uhr" has consistent spacing
    entry = re.sub(r'\s*Uhr\s+', ' Uhr ', entry)
    
    # Limit length to ~150 chars (but at word boundary)
    if len(entry) > 150:
        entry = entry[:150].rsplit(' ', 1)[0]
    
    return entry.strip()


def extract_clean_times(raw_entries: list) -> list:
    """Extract and deduplicate time entries from raw data."""
    if not raw_entries:
        return []
    
    # Pattern: HH:MM - HH:MM Uhr [Description]
    time_pattern = re.compile(
        r'(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*Uhr\s+[^;,]*?)(?=\d{1,2}:\d{2}\s*[-–]|$)',
        re.IGNORECASE
    )
    
    # Combine all entries
    combined = " ".join(str(e) for e in raw_entries if e)
    
    # Normalize first
    combined = re.sub(r'[\n\t\r]+', ' ', combined)
    combined = re.sub(r'\s+', ' ', combined).strip()
    
    # Extract all matches
    matches = time_pattern.findall(combined)
    
    # Deduplicate and clean
    seen = set()
    cleaned = []
    
    for match in matches:
        entry = clean_entry(match)
        
        # Must have a time pattern to be valid
        if not re.search(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', entry):
            continue
        
        # Deduplicate
        entry_key = entry.lower()
        if entry_key not in seen:
            seen.add(entry_key)
            cleaned.append(entry)
    
    return cleaned


def main():
    if not DATA_PATH.exists():
        print(f"Error: {DATA_PATH} not found")
        return
    
    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"Cleaning {len(data)} pools...\n")
    
    for pool in data:
        pool_name = pool.get("name", "Unknown")
        print(f"Processing: {pool_name}")
        
        # Clean each day's entries
        for weekday in WEEKDAYS:
            raw = pool["hours"].get(weekday, [])
            if raw:
                cleaned = extract_clean_times(raw)
                pool["hours"][weekday] = cleaned
                
                if cleaned:
                    preview = "; ".join(cleaned)
                    if len(preview) > 60:
                        preview = preview[:60] + "..."
                    print(f"  {weekday}: {len(cleaned)} entry(ies) → {preview}")
                else:
                    print(f"  {weekday}: cleaned to empty")
            else:
                pool["hours"][weekday] = []
    
    # Write back
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Cleaned data written to {DATA_PATH}")


if __name__ == "__main__":
    main()
