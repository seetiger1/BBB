"""
MINIMALBEISPIEL: Strukturelle Extraktion der Öffnungszeiten ohne Regex-Fallstricke.
Garantiert keine Zeitmischung zwischen Tagen - rein tabellenbasiert.
"""

from bs4 import BeautifulSoup
from typing import Dict, List


def parse_opening_hours_table(html: str) -> Dict[str, List[str]]:
    """
    Extrahiert Öffnungszeiten STRUKTURELL aus Tabelle.
    Keine Regex, keine Textmuster - rein DOM-Navigation.
    
    Grundprinzip:
    1. Finde Öffnungszeiten-Tabelle
    2. Identifiziere Spalten-zu-Tag-Zuordnung aus Header
    3. Iteriere Zeilen und extrahiere Zellinhalt pro Tag
    4. Trenne mehrere Einträge pro Tag durch \n-Split in Zelltext
    """
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Wochentage in erwarteter Reihenfolge
    weekday_names = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    result = {day: [] for day in weekday_names}
    
    # === SCHRITT 1: Finde die Öffnungszeiten-Tabelle ===
    tables = soup.find_all('table')
    
    opening_table = None
    for table in tables:
        # Suche nach Tabelle mit Wochentag-Referenzen
        if any(day.lower() in table.get_text().lower() for day in weekday_names):
            opening_table = table
            break
    
    if not opening_table:
        return result  # Keine Tabelle gefunden
    
    # === SCHRITT 2: Header-Zeile analysieren ===
    rows = opening_table.find_all('tr')
    if not rows:
        return result
    
    header_row = rows[0]
    header_cells = header_row.find_all(['th', 'td'])
    
    # Bestimme Spalten-Zuordnung
    column_to_weekday = {}  # {column_index: 'Montag'}
    
    for col_idx, header_cell in enumerate(header_cells):
        header_text = header_cell.get_text(strip=True).lower()
        
        # Suche nach Wochentag-Abkürzung oder Name
        for weekday in weekday_names:
            abbr = weekday.lower()[:2]  # "mo", "di", "mi", "do", "fr", "sa", "so"
            
            if abbr in header_text or weekday.lower() in header_text:
                column_to_weekday[col_idx] = weekday
                break
    
    # Fallback: wenn nur 7 Spalten vorhanden, ordne sie sequenziell
    if not column_to_weekday and len(header_cells) >= 7:
        for idx in range(7):
            column_to_weekday[idx] = weekday_names[idx]
    
    # === SCHRITT 3: Datensätze extrahieren ===
    for data_row in rows[1:]:
        cells = data_row.find_all(['th', 'td'])
        
        for col_idx, weekday in column_to_weekday.items():
            if col_idx >= len(cells):
                continue
            
            cell = cells[col_idx]
            
            # Hole gesamten Text aus Zelle, mit \n für Zeilenumbrüche
            cell_text = cell.get_text(separator='\n', strip=True)
            
            # Teile mehrere Einträge durch Newlines
            if cell_text and cell_text.lower() not in ['geschlossen', '-', 'ruhetag']:
                entries = [entry.strip() for entry in cell_text.split('\n') 
                          if entry.strip() and entry.strip().lower() not in ['geschlossen', '-']]
                
                result[weekday].extend(entries)
    
    return result


# ============ CLEAN CODE BEISPIEL ============

def get_pool_hours_clean(html: str) -> Dict[str, List[str]]:
    """
    Vereinfachte, produktive Version.
    Eingabe: HTML-String
    Ausgabe: {Wochentag: [Zeit1, Zeit2, ...]}
    """
    soup = BeautifulSoup(html, 'html.parser')
    days = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    hours = {day: [] for day in days}
    
    # Finde Tabelle mit Wochentagen
    table = next(
        (t for t in soup.find_all('table') 
         if any(d.lower() in t.get_text().lower() for d in days)),
        None
    )
    
    if not table:
        return hours
    
    rows = table.find_all('tr')
    headers = rows[0].find_all(['th', 'td']) if rows else []
    
    # Map: column_index -> Wochentag
    col_map = {
        i: day for i, header in enumerate(headers)
        for day in days
        if day.lower()[:2] in header.get_text().lower()
    }
    
    # Fallback
    if not col_map and len(headers) >= 7:
        col_map = {i: days[i] for i in range(7)}
    
    # Daten auslesen
    for row in rows[1:]:
        cells = row.find_all(['th', 'td'])
        for col_idx, day in col_map.items():
            if col_idx < len(cells):
                text = cells[col_idx].get_text(separator='\n', strip=True)
                if text and text.lower() not in ['geschlossen', '-', 'ruhetag']:
                    hours[day].extend(line.strip() for line in text.split('\n') if line.strip())
    
    return hours


# ============ NUTZUNGSBEISPIEL ============

if __name__ == '__main__':
    import requests
    
    url = "https://www.berlinerbaeder.de/baeder/detail/schwimmhalle-fischerinsel/"
    
    try:
        html = requests.get(url, timeout=10).text
        
        # Hauptfunktion nutzen
        opening_hours = parse_opening_hours_table(html)
        
        print("Schwimmhalle Fischerinsel - Öffnungszeiten:\n")
        for day in ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']:
            print(f"{day}:")
            if opening_hours[day]:
                for entry in opening_hours[day]:
                    print(f"  {entry}")
            else:
                print("  (keine Einträge)")
    
    except Exception as e:
        print(f"Fehler: {e}")
