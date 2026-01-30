#!/usr/bin/env python3
"""Clean up pools.json by extracting ONLY the relevant times for each weekday."""
import json
import re
from pathlib import Path

data_path = Path("/workspaces/BBB/data/pools.json")

# Load current data
with open(data_path, "r", encoding="utf-8") as f:
    pools = json.load(f)

WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

def extract_day_times(text: str, day: str) -> list:
    """
    Extract ONLY the times that belong to a specific weekday.
    
    Pattern: Look for the day name, then capture times until the next day or a stop marker.
    Example: "Montag 06:30-08:00 Uhr öffentl. Schwimmen 08:00-22:00 Uhr nur Schul-..."
    Should extract: ["06:30-08:00 Uhr öffentl. Schwimmen", "08:00-22:00 Uhr nur Schul-..."]
    But ONLY up to the next weekday or stop marker like "Einlass", "Tag", etc.
    """
    if not text or day not in text:
        return []
    
    # Find all occurrences of this day
    results = []
    day_lower = day.lower()
    text_lower = text.lower()
    
    # Find the position of this day
    start_idx = 0
    while True:
        pos = text_lower.find(day_lower, start_idx)
        if pos == -1:
            break
        
        # Find the end: either the next weekday or end of string
        end_idx = len(text)
        for other_day in WEEKDAYS:
            if other_day != day:
                next_pos = text_lower.find(other_day.lower(), pos + len(day))
                if next_pos != -1 and next_pos < end_idx:
                    end_idx = next_pos
        
        # Extract segment
        segment = text[pos:end_idx].strip()
        
        # Now extract individual time entries from this segment
        # Pattern: TIME RANGE (HH:MM-HH:MM) followed by description until next time or end
        time_pattern = re.compile(r'(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}[^0-9]*?)(?=\d{1,2}:\d{2}|$)', re.DOTALL)
        
        for match in time_pattern.finditer(segment):
            time_entry = match.group(1).strip()
            # Clean up excessive whitespace/newlines
            time_entry = re.sub(r'\s+', ' ', time_entry)
            # If still too long (> 200 chars), truncate
            if len(time_entry) > 200:
                time_entry = time_entry[:200] + "..."
            if time_entry and '00' in time_entry[:5]:  # Ensure it starts with HH:MM
                results.append(time_entry)
        
        start_idx = pos + 1
    
    return results if results else []

# Clean each pool
for pool in pools:
    for day in WEEKDAYS:
        entries = pool["hours"].get(day, [])
        if not isinstance(entries, list):
            entries = [entries]
        
        cleaned = []
        for entry in entries:
            if isinstance(entry, str):
                # Extract only the times relevant to THIS day
                day_specific = extract_day_times(entry, day)
                cleaned.extend(day_specific)
        
        # If no times found, keep original if it's short
        if not cleaned:
            for entry in entries:
                if isinstance(entry, str) and len(entry) < 100:
                    cleaned.append(entry)
        
        pool["hours"][day] = cleaned

# Save cleaned data
with open(data_path, "w", encoding="utf-8") as f:
    json.dump(pools, f, ensure_ascii=False, indent=2)

print(f"✅ Cleaned {len(pools)} pools!")
print("\nOpening hours per pool:")
for pool in pools:
    print(f"\n  {pool['name']}:")
    for day in WEEKDAYS:
        entries = pool["hours"].get(day, [])
        if entries:
            print(f"    {day}: {len(entries)} entry(ies)")
            for entry in entries[:1]:  # Show first entry only
                preview = entry[:80] + "..." if len(entry) > 80 else entry
                print(f"      → {preview}")
        else:
            print(f"    {day}: (no data)")
