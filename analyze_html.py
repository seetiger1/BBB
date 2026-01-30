#!/usr/bin/env python3
"""Analyze HTML structure of Fischerinsel page."""

import requests
from bs4 import BeautifulSoup
import json

url = 'https://www.berlinerbaeder.de/baeder/detail/schwimmhalle-fischerinsel/'
print(f"Fetching {url}...")
resp = requests.get(url, timeout=10)
resp.encoding = resp.apparent_encoding
soup = BeautifulSoup(resp.text, 'html.parser')

print("\n=== SAVING RAW HTML SNIPPET ===\n")

# Finde die Öffnungszeiten Sektion
keywords = ['Öffnungszeiten', 'Montag', 'öffentl']
for kw in keywords:
    elem = soup.find(string=lambda s: s and kw in s)
    if elem:
        print(f"\nFound '{kw}':")
        
        # Gehe nach oben bis zur Tabelle oder Struktur
        parent = elem.parent
        for i in range(10):
            if parent and parent.name in ['table', 'section', 'article', 'div']:
                break
            parent = parent.parent
        
        if parent:
            # Speichere HTML snippet
            html_str = str(parent)
            print(f"Parent: {parent.name}, class={parent.get('class')}")
            print(f"HTML length: {len(html_str)} chars")
            print("\nFirst 2000 chars:")
            print(html_str[:2000])
            
            # Speichere zu Datei für Analyse
            with open('/workspaces/BBB/html_snippet.html', 'w', encoding='utf-8') as f:
                f.write(html_str)
            print("\n✅ Saved to html_snippet.html")
            break

# Detaillierte Tabellen-Analyse
print("\n\n=== DETAILED TABLE ANALYSIS ===\n")

tables = soup.find_all('table')
print(f"Found {len(tables)} tables")

for i, table in enumerate(tables):
    print(f"\n--- Table {i} ---")
    rows = table.find_all('tr')
    print(f"Rows: {len(rows)}")
    
    # Schaue alle Zeilen
    for j, row in enumerate(rows[:15]):  # Nur erste 15
        cells = row.find_all(['td', 'th'])
        row_text = " | ".join(c.get_text(strip=True)[:30] for c in cells)
        print(f"  Row {j}: {row_text}")

print("\n✅ Analysis complete")
