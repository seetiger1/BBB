#!/usr/bin/env python3
"""
Super-strict data cleaning: Extract ONLY complete, non-redundant time entries.
Pattern: "HH:MM - HH:MM Uhr DESCRIPTION" (one per line, no duplicates)
"""
import json
import re
from pathlib import Path
from collections import OrderedDict

data_path = Path("/workspaces/BBB/data/pools.json")

# Load current data
with open(data_path, "r", encoding="utf-8") as f:
    pools = json.load(f)

WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

def extract_clean_times(raw_text: str) -> list:
    """
    Extract ONLY complete time entries from raw text.
    Pattern: "HH:MM - HH:MM Uhr DESCRIPTION" or "HH:MM-HH:MM Uhr DESCRIPTION"
    
    Examples that should match:
    - "06:30 - 08:00 Uhr öffentl. Schwimmen"
    - "08:00 - 22:00 Uhr nur Schul-, Vereins-, Kursbetrieb"
    - "10:30-17:30 Uhr öffentl. Schwimmen mit eingeschränkter Wasserfläche"
    - "Geschlossen"
    """
    if not raw_text:
        return []
    
    # Clean up: remove excessive whitespace, tabs, newlines
    cleaned = re.sub(r'[\n\t\r]+', ' ', raw_text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    times = []
    seen = set()  # Track to avoid duplicates
    
    # Pattern 1: "HH:MM - HH:MM Uhr DESCRIPTION" or "HH:MM-HH:MM Uhr DESCRIPTION"
    time_pattern = re.compile(
        r'(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*Uhr\s+[^,]*?)(?=\d{1,2}:\d{2}\s*[-–]|\s*(?:Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)|$)',
        re.IGNORECASE
    )
    
    for match in time_pattern.finditer(cleaned):
        entry = match.group(1).strip()
        
        # Remove leading weekday name if present
        entry = re.sub(r'^(Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)\s+', '', entry, flags=re.IGNORECASE)
        entry = entry.strip()
        
        # Only keep if it's not too short and contains time pattern
        if len(entry) > 5 and re.search(r'\d{1,2}:\d{2}', entry):
            # Limit length to 120 chars (reasonable line length)
            if len(entry) > 120:
                entry = entry[:120].rsplit(' ', 1)[0]  # Truncate at word boundary
            
            # Deduplicate (case-insensitive)
            entry_key = entry.lower()
            if entry_key not in seen:
                times.append(entry)
                seen.add(entry_key)
    
    # Pattern 2: Check for "Geschlossen"
    if re.search(r'geschlossen', cleaned, re.IGNORECASE):
        if 'Geschlossen' not in times:
            times.append('Geschlossen')
    
    return times

# Clean each pool
for pool in pools:
    print(f"\n📍 {pool['name']}")
    
    for day in WEEKDAYS:
        entries = pool["hours"].get(day, [])
        if not isinstance(entries, list):
            entries = [entries]
        
        # Combine all entries for this day into one text
        combined_text = " ".join(str(e) for e in entries if e)
        
        # Extract clean times
        cleaned = extract_clean_times(combined_text)
        pool["hours"][day] = cleaned
        
        # Debug output
        if cleaned:
            print(f"  ✅ {day}: {len(cleaned)} entry(ies)")
            for entry in cleaned:
                preview = entry[:90] + "..." if len(entry) > 90 else entry
                print(f"     → {preview}")
        else:
            print(f"  ⚠️  {day}: (no data)")

# Save cleaned data
with open(data_path, "w", encoding="utf-8") as f:
    json.dump(pools, f, ensure_ascii=False, indent=2)

print(f"\n✅ Done! Cleaned {len(pools)} pools and saved to {data_path}")

