#!/usr/bin/env python3
"""Debug HTML structure of Fischerinsel page."""

import requests
from bs4 import BeautifulSoup
import json

url = 'https://www.berlinerbaeder.de/baeder/detail/schwimmhalle-fischerinsel/'
print(f"Fetching {url}...")
resp = requests.get(url, timeout=10)
resp.encoding = resp.apparent_encoding
soup = BeautifulSoup(resp.text, 'html.parser')

print("\n=== Looking for opening hours structure ===\n")

# Suche nach Elementen mit bestimmten Klassen
for pattern in ['rowgroup', 'even', 'day', 'time', 'hours']:
    found = soup.find_all(class_=lambda x: x and pattern in x.lower())
    if found:
        print(f"Found {len(found)} elements with '{pattern}' in class:")
        for i, elem in enumerate(found[:3]):
            print(f"  [{i}] {elem.name} class={elem.get('class')} text={elem.get_text(strip=True)[:60]}")
        print()

# Suche nach Tabellen
print("=== Tables found ===")
tables = soup.find_all('table')
print(f"Total tables: {len(tables)}")

for i, table in enumerate(tables[:3]):
    print(f"\nTable {i}:")
    print(f"  Classes: {table.get('class')}")
    # Schaue nach Headers
    headers = table.find_all('th')
    if headers:
        print(f"  Headers: {[h.get_text(strip=True) for h in headers[:5]]}")
    # Schaue nach Zeilen
    rows = table.find_all('tr')
    print(f"  Rows: {len(rows)}")
    # Zeige erste 3 Zeilen
    for j, row in enumerate(rows[:3]):
        cells = row.find_all(['td', 'th'])
        print(f"    Row {j}: {[c.get_text(strip=True)[:40] for c in cells[:5]]}")

# Suche direkt nach "Montag", "Öffnungszeiten"
print("\n=== Direct text search ===")
for keyword in ['Montag', 'Dienstag', 'Öffnungszeiten', 'öffentl', 'Schul']:
    elem = soup.find(string=lambda s: s and keyword in s)
    if elem:
        print(f"\nFound '{keyword}' in {elem.parent.name}")
        # Zeige Parent-Struktur
        parent = elem.parent
        for level in range(5):
            if parent:
                print(f"  {'  '*level}{parent.name} {parent.get('class', [])}")
                parent = parent.parent

# Suche nach div mit bestimmten Datenattributen
print("\n=== All divs with data attributes ===")
divs = soup.find_all('div', attrs={'data-days': True})
print(f"Found {len(divs)} divs with data-days attribute")
if divs:
    print(f"First one: {divs[0].get('data-days')[:200]}")

# Alternative: Schaue nach strukturierten daten/JSON
print("\n=== Script tags with JSON/LD ===")
scripts = soup.find_all('script', type='application/ld+json')
print(f"Found {len(scripts)} LD-JSON scripts")

# Schaue allgemein nach allen interessanten Struktur-Hinweisen
print("\n=== All unique class names containing relevant keywords ===")
all_classes = set()
for elem in soup.find_all(class_=True):
    classes = elem.get('class', [])
    for cls in classes:
        if any(kw in cls.lower() for kw in ['day', 'time', 'hour', 'row', 'even', 'odd', 'pool']):
            all_classes.add(cls)

for cls in sorted(all_classes):
    print(f"  - {cls}")
