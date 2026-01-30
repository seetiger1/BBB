"""
Extraktion von Öffnungszeiten aus der Schwimmhalle Fischerinsel Tabelle.
Strukturelle Analyse ohne Regex - garantiert keine Zeitmischung zwischen Tagen.
"""

from bs4 import BeautifulSoup
from typing import Dict, List
import requests


def extract_opening_hours(html: str) -> Dict[str, List[str]]:
    """
    Extrahiert Öffnungszeiten aus HTML-Tabelle.
    
    Rückgabe:
    {
        'Montag': ['06:30 - 08:00 Uhr öffentl. Schwimmen', '08:00 - 22:00 Uhr nur Schul-', ...],
        'Dienstag': [...],
        ...
    }
    """
    
    soup = BeautifulSoup(html, 'html.parser')
    weekdays = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    opening_hours = {day: [] for day in weekdays}
    
    # Finde die Öffnungszeiten-Tabelle
    # Strategie: Suche nach table mit Kontext "Öffnungszeiten" oder "Öffnungszeit"
    tables = soup.find_all('table')
    
    opening_hours_table = None
    
    # Suche die richtige Tabelle (mit Wochentagen als Header oder Inhalt)
    for table in tables:
        table_text = table.get_text()
        
        # Prüfe, ob Tabelle Wochentag-Namen enthält
        if any(day.lower() in table_text.lower() for day in weekdays):
            opening_hours_table = table
            break
    
    if not opening_hours_table:
        return opening_hours
    
    # Analysiere Tabellenstruktur
    rows = opening_hours_table.find_all('tr')
    
    # Methode 1: Header-Row mit Wochentagen in <th> oder <td>
    header_row = rows[0] if rows else None
    
    if header_row:
        header_cells = header_row.find_all(['th', 'td'])
        
        # Bestimme Spalten-Zuordnung (welche Spalte = welcher Tag)
        column_to_day = {}
        
        for col_idx, cell in enumerate(header_cells):
            cell_text = cell.get_text(strip=True).lower()
            
            for day_idx, day in enumerate(weekdays):
                if day.lower()[:3] in cell_text or day.lower() in cell_text:
                    column_to_day[col_idx] = day
                    break
        
        # Wenn keine Header gefunden, fallback zu Standard (Mo=0, Di=1, etc.)
        if not column_to_day and len(header_cells) >= 7:
            for col_idx in range(min(7, len(header_cells))):
                column_to_day[col_idx] = weekdays[col_idx]
        
        # Extrahiere Zeiteinträge aus Datensätzen (Zeilen ab Zeile 1)
        for row_idx, row in enumerate(rows[1:], start=1):
            cells = row.find_all(['th', 'td'])
            
            for col_idx, cell in enumerate(cells):
                if col_idx not in column_to_day:
                    continue
                
                day = column_to_day[col_idx]
                
                # Extrahiere ALLE Einträge aus dieser Zelle
                # Strategie: Suche nach Zeitmuster "HH:MM - HH:MM"
                cell_text = cell.get_text(separator='\n', strip=True)
                
                if not cell_text or cell_text.lower() == 'geschlossen':
                    continue
                
                # Mehrzeilen-Einträge durch \n getrennt
                entries = [line.strip() for line in cell_text.split('\n') if line.strip()]
                
                for entry in entries:
                    # Validiere: Beginnt mit Zeitformat oder ist Beschreibung für vorherige Zeit
                    if entry and not entry.lower().startswith('nur') and not entry.lower().startswith('inklusive'):
                        opening_hours[day].append(entry)
    
    return opening_hours


def extract_opening_hours_alternative(html: str) -> Dict[str, List[str]]:
    """
    Alternative Methode: Direkter Zugriff auf Zellen mit Wochentag-Spalte.
    Verwendet Regex nur für Zeitformat-Validierung, KEINE Extraktionsmethode.
    """
    import re
    
    soup = BeautifulSoup(html, 'html.parser')
    weekdays = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    opening_hours = {day: [] for day in weekdays}
    
    # Finde die Öffnungszeiten-Tabelle (annahme: erste Tabelle mit 7 Spalten oder ähnlich)
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        
        if not rows:
            continue
        
        # Heuristische Prüfung: Tabelle mit Wochentagen
        all_cells = rows[0].find_all(['th', 'td'])
        
        if len(all_cells) < 7:
            continue
        
        # Versuche Header zu ermitteln
        header_text = ' '.join(cell.get_text(strip=True) for cell in all_cells)
        
        if not any(day.lower()[:2] in header_text.lower() for day in weekdays):
            continue
        
        # ============ STRUKTURELLE EXTRAKTION ============
        
        # Finde Spalten-Indizes für jeden Wochentag
        column_mapping = {}
        
        for col_idx, cell in enumerate(all_cells):
            cell_text = cell.get_text(strip=True).lower()
            
            for day in weekdays:
                day_abbr = day.lower()[:2]  # "mo", "di", "mi", etc.
                if day_abbr in cell_text:
                    column_mapping[day] = col_idx
                    break
        
        # Fallback: wenn keine Tage gefunden, nutze Spalten 0-6
        if not column_mapping:
            if len(all_cells) >= 7:
                for idx, day in enumerate(weekdays):
                    column_mapping[day] = idx
        
        # Extrahiere aus allen Datenzeilen (ab Zeile 1)
        for row in rows[1:]:
            cells = row.find_all(['th', 'td'])
            
            for day, col_idx in column_mapping.items():
                if col_idx >= len(cells):
                    continue
                
                cell = cells[col_idx]
                
                # Hole ALLE Text-Knoten aus der Zelle
                # Wichtig: Nicht nur .get_text(), sondern iteriere über direkte Children
                texts = []
                
                for content in cell.children:
                    if isinstance(content, str):
                        text = content.strip()
                        if text:
                            texts.append(text)
                    elif hasattr(content, 'get_text'):
                        text = content.get_text(strip=True)
                        if text:
                            texts.append(text)
                
                # Wenn keine texte via children, nutze get_text mit Separator
                if not texts:
                    full_text = cell.get_text(separator='\n', strip=True)
                    if full_text:
                        texts = [t.strip() for t in full_text.split('\n') if t.strip()]
                
                # Filtere und validiere Einträge
                for text in texts:
                    if text.lower() in ['geschlossen', '-', 'ruhetag']:
                        continue
                    
                    # Nur hinzufügen wenn Text nicht leer und nicht bloß Beschreibung
                    if text:
                        opening_hours[day].append(text)
    
    return opening_hours


# ============ BEISPIELNUTZUNG ============

if __name__ == '__main__':
    # Beispiel mit URL
    url = "https://www.berlinerbaeder.de/baeder/detail/schwimmhalle-fischerinsel/"
    
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'
        html = response.text
        
        # Methode 1
        hours_1 = extract_opening_hours(html)
        
        print("=== METHODE 1: Basis-Strukturanalyse ===")
        for day, times in hours_1.items():
            if times:
                print(f"{day}:")
                for time in times:
                    print(f"  - {time}")
            else:
                print(f"{day}: (Keine Einträge)")
        
        print("\n" + "="*50 + "\n")
        
        # Methode 2
        hours_2 = extract_opening_hours_alternative(html)
        
        print("=== METHODE 2: Alternative Strukturanalyse ===")
        for day, times in hours_2.items():
            if times:
                print(f"{day}:")
                for time in times:
                    print(f"  - {time}")
            else:
                print(f"{day}: (Keine Einträge)")
        
    except Exception as e:
        print(f"Fehler beim Abrufen: {e}")
        print("\nFür lokale HTML-Dateien: html mit open() laden und an Funktionen übergeben")
