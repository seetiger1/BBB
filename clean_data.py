#!/usr/bin/env python3
"""Clean up pools.json by extracting only meaningful times from bloated entries."""
import json
import re
from pathlib import Path

data_path = Path("/workspaces/BBB/data/pools.json")

# Load current data
with open(data_path, "r", encoding="utf-8") as f:
    pools = json.load(f)

# Regex to match time patterns
time_regex = re.compile(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}')

# Clean each pool
for pool in pools:
    for day, entries in pool["hours"].items():
        if not isinstance(entries, list):
            entries = [entries]
        
        # Filter: keep only entries that contain time patterns
        cleaned = []
        for entry in entries:
            if isinstance(entry, str) and time_regex.search(entry):
                # For long entries, try to extract just the meaningful line
                if len(entry) > 150:
                    # Try to extract just the line with weekday + times
                    lines = entry.split(" ")
                    relevant = []
                    capture = False
                    for word in lines:
                        if day.lower() in word.lower():
                            capture = True
                        if capture:
                            relevant.append(word)
                            if len(" ".join(relevant)) > 100:
                                break
                    if relevant:
                        cleaned.append(" ".join(relevant))
                    else:
                        cleaned.append(entry[:150])
                else:
                    cleaned.append(entry)
        
        pool["hours"][day] = cleaned if cleaned else []

# Save cleaned data
with open(data_path, "w", encoding="utf-8") as f:
    json.dump(pools, f, ensure_ascii=False, indent=2)

print(f"✅ Cleaned {len(pools)} pools!")
for pool in pools:
    print(f"  - {pool['name']}: Montag={len(pool['hours'].get('Montag', []))} entries")
