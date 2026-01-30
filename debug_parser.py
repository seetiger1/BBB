#!/usr/bin/env python3
"""Debug script to see what the parser extracts."""

import requests
from bs4 import BeautifulSoup
import re

url = 'https://www.berlinerbaeder.de/baeder/detail/schwimmhalle-fischerinsel/'
resp = requests.get(url, timeout=10)
resp.encoding = resp.apparent_encoding
soup = BeautifulSoup(resp.text, 'html.parser')

full_text = soup.get_text(separator="\n", strip=True)

# Normalize
full_text = re.sub(r'\n\s*\n+', '\n', full_text)
full_text = re.sub(r'[ \t]+', ' ', full_text)

lines = full_text.split('\n')

print("=" * 80)
print("SEARCHING FOR WEEKDAY NAMES IN TEXT")
print("=" * 80)

WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

for i, line in enumerate(lines):
    line_stripped = line.strip()
    for wd in WEEKDAYS:
        if wd.lower() in line_stripped.lower():
            print(f"\nLine {i}: Found '{wd}'")
            print(f"  Content: {line_stripped[:100]}")
            # Show next 5 lines
            for j in range(1, 6):
                if i + j < len(lines):
                    next_line = lines[i + j].strip()
                    print(f"  Line {i+j}: {next_line[:100]}")
            break

print("\n" + "=" * 80)
print("SEARCHING FOR TIME PATTERNS")
print("=" * 80)

time_pattern = re.compile(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}')

time_matches = 0
for i, line in enumerate(lines):
    if time_pattern.search(line):
        time_matches += 1
        print(f"Line {i}: {line[:100]}")

print(f"\nTotal lines with time pattern: {time_matches}")

print("\n" + "=" * 80)
print("SAMPLE TEXT (first 3000 chars)")
print("=" * 80)
print(full_text[:3000])
