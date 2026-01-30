#!/usr/bin/env python3
"""
Strict cleaner with plausibility checks.
Ensures data quality and reasonable entry counts per day.
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

# Plausibility rules
MIN_ENTRIES_PER_DAY = 1
MAX_ENTRIES_PER_DAY = 4


def is_valid_entry(entry: str) -> bool:
    """Validate a single entry."""
    if not entry or len(entry) < 8:
        return False
    
    # Must have time pattern
    if not re.search(r'\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}', entry):
        return False
    
    return True


def clean_entry(entry: str) -> str:
    """Normalize entry."""
    if not isinstance(entry, str):
        return ""
    
    entry = entry.strip()
    
    # Remove weekday names
    entry = re.sub(rf'^({"|".join(WEEKDAYS)})\s*', '', entry, flags=re.IGNORECASE).strip()
    
    # Normalize whitespace
    entry = re.sub(r'[\n\t\r]+', ' ', entry)
    entry = re.sub(r'\s+', ' ', entry).strip()
    
    # Normalize time separator
    entry = re.sub(r'\s*[–—-]\s*', ' - ', entry)
    
    # Ensure "Uhr" spacing
    entry = re.sub(r'\s+[Uu]hr\s+', ' Uhr ', entry)
    entry = re.sub(r'([0-9])([Uu]hr)', r'\1 \2', entry)
    
    # Remove trailing junk
    entry = re.sub(r'[,;\.]+\s*$', '', entry)
    
    # Truncate at word boundary if too long
    if len(entry) > 120:
        entry = entry[:120].rsplit(' ', 1)[0]
    
    return entry.strip()


def main():
    if not DATA_PATH.exists():
        print(f"❌ {DATA_PATH} not found")
        return
    
    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"Cleaning {len(data)} pools with plausibility checks...\n")
    
    for pool in data:
        pool_name = pool.get("name", "Unknown")
        print(f"📍 {pool_name}")
        
        # Clean each day
        for weekday in WEEKDAYS:
            raw_entries = pool["hours"].get(weekday, [])
            
            # Clean and validate
            cleaned = []
            seen = set()
            
            for raw_entry in raw_entries:
                if not isinstance(raw_entry, str):
                    continue
                
                # Split by semicolon in case multiple entries concatenated
                for part in raw_entry.split(';'):
                    part = part.strip()
                    if not part:
                        continue
                    
                    cleaned_entry = clean_entry(part)
                    
                    # Validate
                    if not is_valid_entry(cleaned_entry):
                        continue
                    
                    # Deduplicate
                    key = cleaned_entry.lower()
                    if key not in seen:
                        seen.add(key)
                        cleaned.append(cleaned_entry)
            
            # Apply plausibility check
            if len(cleaned) > MAX_ENTRIES_PER_DAY:
                print(f"  ⚠️  {weekday}: {len(cleaned)} entries (max={MAX_ENTRIES_PER_DAY}) - truncating")
                cleaned = cleaned[:MAX_ENTRIES_PER_DAY]
            elif len(cleaned) > 0:
                print(f"  ✅ {weekday}: {len(cleaned)} entry/entries")
            else:
                print(f"  ⚠️  {weekday}: [empty]")
            
            pool["hours"][weekday] = cleaned
    
    # Write back
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Cleaned and saved to {DATA_PATH}")
    
    # Validation summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    for pool in data:
        pool_name = pool.get("name", "")
        montag_count = len(pool["hours"].get("Montag", []))
        print(f"\n{pool_name}")
        print(f"  Montag: {montag_count} entries")
        if montag_count < MIN_ENTRIES_PER_DAY or montag_count > MAX_ENTRIES_PER_DAY:
            print(f"    ⚠️  WARNING: Outside plausible range [{MIN_ENTRIES_PER_DAY}, {MAX_ENTRIES_PER_DAY}]")
        else:
            print(f"    ✅ OK")


if __name__ == "__main__":
    main()
