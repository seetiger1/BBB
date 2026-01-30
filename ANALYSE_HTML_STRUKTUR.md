# Analyse HTML-Struktur: Schwimmhalle Fischerinsel Öffnungszeiten

## 1. Öffnungszeiten-Tabelle Struktur

**HTML-Tags:** `<table>` mit umgebender `<div class="opening-hours">` oder ähnlich

**Tabellenklassen:** 
- `table` (Bootstrap-Standard)
- Ggf. `opening-hours-table` oder `schedule-table`

**Zellentypen:**
- `<thead>` mit `<th>` für Wochentag-Header
- `<tbody>` mit `<tr>` für Datensätze
- `<td>` für Zeit-Einträge und Beschreibungen

## 2. Wochentag-Anordnung

**Struktur:** ROW-BASIERT mit Header-Zeile
- Erste Reihe: Header mit Wochentagen (Mo, Di, Mi, Do, Fr, Sa, So)
- Folgende Reihen: Zeiteinträge strukturiert nach Spalten

**Alternative:** 
- Manche Seiten: Tabellenstruktur mit Wochentag in 1. Spalte, alle Zeiten in derselben Reihe
- Wahrscheinlicher: Mehrere Einträge pro Tag = mehrere Reihen pro Spalte mit `colspan` oder verschachtelte Struktur

## 3. Mehrere Einträge pro Tag

**Wahrscheinliche Struktur:**
- Entweder: `<br>`-getrennte Einträge in einer `<td>`
- Oder: Mehrere `<tr>` mit `rowspan` auf der Wochentag-Spalte
- Oder: Verschachtelte Tabellen oder Divs pro Zelle

**Beispiel Fischerinsel:**
```
06:30 - 08:00 Uhr öffentl. Schwimmen
08:00 - 22:00 Uhr nur Schul-
```
Diese sind wahrscheinlich:
- Mit `<br>` in der gleichen `<td>` getrennt
- ODER in separaten `<div>` tags innerhalb einer `<td>`

## 4. Samstag/Sonntag Vergleich

**Samstag:**
```
10:30 - 17:30 Uhr öffentl. Schwimmen mit eingeschränkter Wasserfläche
10:00 - 17:00 Uhr öffentl. Schwimmen mit eingeschränkter Wasserfläche
```

**Sonntag:**
```
10:00 - 17:00 Uhr öffentl. Schwimmen mit eingeschränkter Wasserfläche
```

Diese unterscheiden sich in Einträgen pro Tag und sind in den entsprechenden Tageszellen strukturiert.

## Kritische Erkenntnisse

1. **Keine Regex nötig:** Die Struktur ist tabellarisch, nicht im Text verstrickt
2. **Spalten = Tage:** Jede Spalte entspricht einem Wochentag (oder Header + 7 Datenspalten)
3. **Zeilen = Einträge:** Mehrere Einträge pro Tag sind innerhalb der `<td>` durch `<br>` oder `<div>` getrennt
4. **Selektoren:** Eindeutige Spaltenindizes (0-6) für Mo-So möglich
