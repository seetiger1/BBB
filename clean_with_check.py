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
    
    # Remove leading weekday names and duplicated weekday tokens like "Sonntag Sonntag"
    entry = re.sub(rf'^({"|".join(WEEKDAYS)})\s*', '', entry, flags=re.IGNORECASE).strip()
    entry = re.sub(rf'\b({'|'.join(WEEKDAYS)})\b\s+\1\b', r'\1', entry, flags=re.IGNORECASE)
    
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


def normalize_description(entry: str) -> str:
    """Normalize common description variants to a short canonical form.

    Examples:
      - "öffentl. Schwimmen mit eingeschränkter Wasserfläche" -> "öffentl. Schwimmen (eingeschr. WF)"
      - "nur Schul-, Vereins-, Kursbetrieb" variants -> "nur Schul-/Vereins-/Kursbetrieb"
    """
    # Split time part and description
    m = re.match(r"^(\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}[^\s]*)(?:\s+(.*))?", entry)
    if not m:
        return entry

    time_part = m.group(1).strip()
    desc = (m.group(2) or "").strip()

    desc_l = desc.lower()

    # Normalize common phrases
    if not desc_l:
        normalized_desc = ""
    elif 'eingeschränk' in desc_l or 'eingeschraenk' in desc_l or 'eingeschr' in desc_l:
        # public swimming with restricted water surface
        if 'öffent' in desc_l or 'offent' in desc_l:
            normalized_desc = 'öffentl. Schwimmen (eingeschr. WF)'
        else:
            normalized_desc = 'öffentl. Schwimmen (eingeschr. WF)'
    elif any(k in desc_l for k in ['schul', 'verein', 'kurs']):
        normalized_desc = 'nur Schul-/Vereins-/Kursbetrieb'
    elif 'gemischt' in desc_l:
        normalized_desc = 'gemischt'
    elif 'menschen mit behinderung' in desc_l or 'behinderung' in desc_l:
        normalized_desc = 'Menschen mit Behinderung'
    elif 'öffent' in desc_l or 'offent' in desc_l:
        normalized_desc = 'öffentl. Schwimmen'
    else:
        # Fallback: shorten long descriptions
        normalized_desc = desc.split(' Einlass', 1)[0].split(' Badeschluss', 1)[0]
        normalized_desc = normalized_desc[:80].rsplit(' ', 1)[0]

    if normalized_desc:
        return f"{time_part} {normalized_desc}"
    return time_part


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
            raw_count = len(raw_entries) if isinstance(raw_entries, list) else 0
            
            # Clean and validate
            cleaned = []
            seen = set()
            
            for raw_entry in raw_entries:
                if not isinstance(raw_entry, str):
                    continue
                
                # Check for "Geschlossen" first - preserve it as-is
                if 'geschlossen' in raw_entry.lower():
                    cleaned.append("Geschlossen")
                    continue
                
                # Split by semicolon first
                semiparts = [p.strip() for p in raw_entry.split(';') if p.strip()]
                for part in semiparts:
                    # If a part contains multiple time windows concatenated (e.g. "06:30 - 16:00 ... 16:00 - 22:00 ..."),
                    # split them using a time-based regex with lookahead.
                    multi_pattern = re.compile(r'(\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}(?:\s+[Uu]hr)?\s*.*?)(?=\d{1,2}:\d{2}\s*[-–]|$)', re.IGNORECASE)
                    submatches = multi_pattern.findall(part)
                    if submatches:
                        candidates = [s.strip() for s in submatches if s.strip()]
                    else:
                        candidates = [part]

                    for cand in candidates:
                        cleaned_entry = clean_entry(cand)
                        # Normalize description variants
                        normalized_entry = normalize_description(cleaned_entry)

                        # Validate
                        if not is_valid_entry(normalized_entry):
                            continue

                        # Deduplicate
                        key = normalized_entry.lower()
                        if key not in seen:
                            seen.add(key)
                            cleaned.append(normalized_entry)
            
            # Apply plausibility check
            if len(cleaned) > MAX_ENTRIES_PER_DAY:
                print(f"  ⚠️  {weekday}: {len(cleaned)} entries (max={MAX_ENTRIES_PER_DAY}) - truncating")
                cleaned = cleaned[:MAX_ENTRIES_PER_DAY]
            
            # If completely empty and not "Geschlossen", add "?" to indicate missing data
            if len(cleaned) == 0 and raw_count == 0:
                cleaned = ["?"]
            
            if len(cleaned) > 0:
                print(f"  ✅ {weekday}: {len(cleaned)} entry/entries")
            else:
                print(f"  ⚠️  {weekday}: [empty]")

            # Debug: if raw had more entries than cleaned, show what was removed
            if raw_count != len(cleaned):
                print(f"    (raw: {raw_count} -> cleaned: {len(cleaned)})")
                if raw_count > 0:
                    # print raw sample
                    sample = raw_entries if raw_count <= 5 else raw_entries[:5]
                    print(f"    raw sample: {sample}")
            
            # Post-process: sort by start time and apply weekend preference rules
            def start_minutes(e: str) -> int:
                m = re.search(r"(\d{1,2}):(\d{2})", e)
                if not m:
                    return 24 * 60
                return int(m.group(1)) * 60 + int(m.group(2))

            # If weekend and public-swimming exists, prefer public entries and drop 'nur Schul' entries
            if weekday in ("Samstag", "Sonntag"):
                lowers = [e.lower() for e in cleaned]
                if any('öffent' in s or 'öffentl' in s for s in lowers):
                    cleaned = [e for e in cleaned if 'nur schul' not in e.lower()]

            # Sort by start time
            cleaned.sort(key=start_minutes)

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
