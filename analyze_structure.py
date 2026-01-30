import requests
from bs4 import BeautifulSoup
import json

url = "https://www.berlinerbaeder.de/baeder/detail/schwimmhalle-fischerinsel/"

try:
    response = requests.get(url, timeout=10)
    response.encoding = 'utf-8'
    html = response.text
    
    # Speichere HTML zum Debugging
    with open('/workspaces/BBB/pool_page.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Finde alle Tabellen
    tables = soup.find_all('table')
    print(f"Gefundene Tabellen: {len(tables)}\n")
    
    # Analysiere jede Tabelle
    for i, table in enumerate(tables):
        print(f"=== TABELLE {i} ===")
        print(f"Tabellen-Klassen: {table.get('class', [])}\n")
        
        # Zeige Struktur
        print("HTML-Struktur der ersten 10 Reihen:")
        rows = table.find_all('tr')
        for j, row in enumerate(rows[:10]):
            print(f"\nRow {j}:")
            cells = row.find_all(['th', 'td'])
            for k, cell in enumerate(cells):
                classes = cell.get('class', [])
                text = cell.get_text(strip=True)[:100]
                print(f"  Cell {k}: tag={cell.name}, class={classes}, text='{text}'")
        
        print(f"\nGesamt Reihen: {len(rows)}\n")
        print("=" * 60 + "\n")

except Exception as e:
    print(f"Fehler: {e}")
    import traceback
    traceback.print_exc()
