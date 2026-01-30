#!/usr/bin/env python3
"""
Strict data cleaner: Extract ONLY valid time entries with proper formatting.
Separates entries by semicolon when multiple exist for one day.
"""

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


def is_valid_entry(entry: str) -> bool:
    """Check if entry is a valid opening hours entry."""
    if not entry or len(entry) < 8:
        return False
    
    # Must have time pattern HH:MM - HH:MM (or HH:MM-HH:MM)
    if not re.search(r'\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}', entry):
        return False
    
    # Should ideally have "Uhr" but accept if it clearly looks like times
    # (sometimes description is missing)
    
    return True


def clean_entry(entry: str) -> str:
    """Normalize a single entry."""
    if not entry or not isinstance(entry, str):
        return ""
    
    entry = entry.strip()
    
    # Remove leading/trailing weekday names
    entry = re.sub(rf'^({"|".join(WEEKDAYS)})\s*', '', entry, flags=re.IGNORECASE).strip()
    
    # Normalize whitespace
    entry = re.sub(r'[\n\t\r]+', ' ', entry)
    entry = re.sub(r'\s+', ' ', entry).strip()
    
    # Normalize time separator
    entry = re.sub(r'\s*[–—-]\s*', ' - ', entry)
    
    # Ensure "Uhr" has consistent spacing
    entry = re.sub(r'\s+[Uu]hr\s+', ' Uhr ', entry)
    
    # Remove any trailing punctuation or extra info beyond description
    # Keep format: "HH:MM - HH:MM Uhr DESCRIPTION"
    # Remove anything after a semicolon, pipe, colon (except in time)
    match = re.match(r'^(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*Uhr\s+[^;|]*?)(?:[;|]|$)', entry)
    if match:
        entry = match.group(1).strip()
    
    # Limit to ~120 chars at word boundary
    if len(entry) > 120:
        entry = entry[:120].rsplit(' ', 1)[0]
    
    return entry.strip()


def main():
    if not DATA_PATH.exists():
        print(f"Error: {DATA_PATH} not found")
        return
    
    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"Cleaning {len(data)} pools...\n")
    
    for pool in data:
        pool_name = pool.get("name", "Unknown")
        print(f"\nPool: {pool_name}")
        print("-" * 60)
        
        # Clean each day's entries
        for weekday in WEEKDAYS:
            raw_entries = pool["hours"].get(weekday, [])
            
            # Clean and deduplicate
            cleaned = []
            seen = set()
            
            for raw_entry in raw_entries:
                if not isinstance(raw_entry, str):
                    continue
                
                # Split by semicolon in case multiple entries concatenated
                parts = raw_entry.split(';')
                
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    
                    # Clean this entry
                    cleaned_entry = clean_entry(part)
                    
                    # Validate
                    if not is_valid_entry(cleaned_entry):
                        continue
                    
                    # Deduplicate
                    key = cleaned_entry.lower()
                    if key not in seen:
                        seen.add(key)
                        cleaned.append(cleaned_entry)
            
            # Update the pool data
            pool["hours"][weekday] = cleaned
            
            # Print for validation
            if cleaned:
                print(f"  {weekday:12} ({len(cleaned):1}): ", end="")
                print("; ".join(cleaned)[:80] + ("..." if sum(len(c) for c in cleaned) > 80 else ""))
            else:
                print(f"  {weekday:12} (0): [empty]")
    
    print("\n" + "=" * 60)
    
    # Write back
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Cleaned and saved to {DATA_PATH}")


if __name__ == "__main__":
    main()
