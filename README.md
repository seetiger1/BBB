# Berliner Bäder — Öffnungszeiten (kleine App)

Kurz: Dieses Repository enthält eine kleine, anfängerfreundliche Webanwendung, die die Öffnungszeiten ausgewählter Berliner Bäder ausliest, in `data/pools.json` cached und per API sowie Next.js-Frontend anzeigt.

**Was das Projekt macht**
- Der Python-Scraper holt detailseiten von Bädern, extrahiert Namen, Öffnungszeiten (pro Wochentag), Quell-URL und Timestamp und speichert die Ergebnisse als UTF-8 JSON in `data/pools.json`.
- Die FastAPI-Anwendung liefert diese gecachten Daten unter `GET /api/pools` aus.
- Die Next.js-Frontendseite (`app/page.tsx`) ruft `/api/pools` ab und zeigt die Liste der Bäder sowie die Öffnungszeiten für den aktuellen Wochentag.

## Datenquelle / wie Daten gesammelt werden
- Daten werden von den offiziellen Detailseiten der Berliner Bäder gelesen (URLs müssen beim Scraper angegeben werden).
- Es gibt kein Live-Scraping auf Frontend-Anfragen: die Anwendung liest nur aus `data/pools.json`.
- Aktualisierungen erfolgen durch geplante Ausführung des Scrapers (z. B. daily via GitHub Actions). Der Scraper ist so defensiv implementiert, dass er bei Strukturänderungen der Seite nicht abstürzt, sondern sinnvolle Fallbacks liefert.

## Dateien im Repo (wichtig)
- `scraper/scrape_pools.py` — Python-Scraper (requests + beautifulsoup4)
- `api/main.py` — FastAPI-Anwendung, liest nur aus `data/pools.json`
- `app/page.tsx` — Next.js App Router Seite (Frontend)
- `data/pools.json` — gecachte Pool-Daten (UTF-8 JSON)
- `requirements.txt` — Python-Abhängigkeiten
- `package.json` — Node/Next.js Abhängigkeiten
- `vercel.json` — einfache Vercel-Konfiguration für das Routing

## Lokales Ausführen (Entwickler)

Python (API + Scraper):
```bash
# optional: erstelle venv
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Scraper: übergebe Pool-Detail-URLs oder --file
python scraper/scrape_pools.py https://example/pool1 https://example/pool2

# Dev-Server für die API
uvicorn api.main:APP --reload --port 8000
# GET http://127.0.0.1:8000/api/pools
```

Frontend (Next.js):
```bash
# Node installieren, dann
npm install
npm run dev
# Öffne http://localhost:3000
```

Hinweis: Das Frontend ruft `/api/pools` relativ ab; in Entwicklung können API (Port 8000) und Frontend (Port 3000) getrennt laufen — für lokale Tests ist es praktisch, `uvicorn` auf Port 3000 zu starten oder ein kleines Proxy-Setup zu verwenden.

## Deployment auf Vercel
- Dieses Repo ist als Mono-Repo für Vercel vorbereitet. `vercel.json` enthält eine einfache Funktionseinstellung, damit `api/main.py` als Python-Funktion ausgeführt werden kann.
- Vercel-Workflow:
  - Frontend (`app/`) wird als Next.js-App deployed.
  - `api/main.py` wird als Python Serverless Function deployed und über die Rewrite-Regel unter `/api/pools` erreichbar.

## Automatisierung (Cron / CI)
- Geplante Updates sollten den Scraper regelmäßig (z. B. täglich) ausführen und die erzeugte `data/pools.json` in den Repo-Branch committen.
- In GitHub Actions wäre ein Job möglich, der:
  1. Python installiert
  2. `pip install -r requirements.txt`
  3. `python scraper/scrape_pools.py --file urls.txt`
  4. `git commit` & `git push` (oder push in einen branch/PR)

## Hinweise & Grenzen
- Der Scraper versucht, Seitenstruktur-Änderungen toleranter zu behandeln, kann aber keine Garantie für 100% exakte Extraktion geben — bei größeren Änderungen sind Anpassungen nötig.
- Es werden keine Datenbanken verwendet; alles wird in `data/pools.json` gecached.

Wenn du möchtest, kann ich jetzt:
- ein Beispiel `urls.txt` anlegen und eine Demo-Ausführung des Scrapers mit 1-2 öffentlichen URLs (wenn du die URLs bereitstellst),
- oder eine GitHub Actions-Workflowdatei anlegen, die den Scraper täglich ausführt.
# BBB