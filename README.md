# Fitness Tracker (Notion-Integration)

Persönliche, passwortgeschützte Web-App zum Erfassen von Trainings und zum Tracken von
Körpergewicht — liest und schreibt direkt in deine bestehenden Notion-Datenbanken.
Keine eigene Datenbank, kein Datenduplikat: Notion bleibt die einzige Quelle der Wahrheit.

## Funktionen

- Login mit einem Passwort (über Environment Variable, kein Notion-eigener Login nötig)
- Trainings erfassen → landet direkt in deiner Notion-Datenbank "Training Sessions"
  (Datum, Dauer, Ziel-Tags, RPE, Schlaf, Körpergewicht am Trainingstag, Notizen)
- Übungen pro Training → landen direkt in "Trainings-Log (Übungen)", verknüpft per Relation
- Körpergewicht-Log → landet in einer neu angelegten Notion-Datenbank "⚖️ Körpergewicht-Log"
  (unabhängig von Trainingstagen, für den echten 7-Tage-Trend)
- Dashboard mit Gewichtsverlauf-Chart und letzten Trainings
- Kraft-Fortschritt pro Übung als Chart (z.B. "Beinpresse" über die Zeit)
- Jede Session-Detailseite verlinkt direkt zur Notion-Seite

## Wie die Verbindung funktioniert

Die App nutzt einen **Notion-Integration-Token**, der ausschließlich serverseitig
verwendet wird (nie im Browser, nie im Frontend-Code). Der Token wird als Environment
Variable gesetzt (`NOTION_TOKEN`) — genau das war der ursprüngliche Blocker beim
HTML-Tracker: Notion-API-Calls direkt aus dem Browser sind unsicher, weil der Token dort
für jeden sichtbar wäre. Mit diesem Flask-Backend bleibt der Token geschützt.

## Notion-Integration einrichten (einmalig)

1. Gehe zu [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. **+ New integration** → Name z.B. "Fitness Tracker App" → Workspace auswählen → Submit
3. Kopiere den **Internal Integration Token** (beginnt mit `ntn_...`) — das ist dein `NOTION_TOKEN`
4. Öffne in Notion jede der drei Datenbanken einzeln:
   - **Training Sessions**
   - **Trainings-Log (Übungen)**
   - **⚖️ Körpergewicht-Log** (wurde für dieses Projekt neu angelegt)
5. Klicke jeweils oben rechts auf **"..."** → **Connections** → **Connect to** → deine
   Integration ("Fitness Tracker App") auswählen

Ohne Schritt 5 bekommt die App bei jedem Zugriff einen 404/403-Fehler von Notion — die
Datenbanken müssen der Integration explizit freigegeben werden.

## Lokal starten

```bash
cd fitness-tracker
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # dann APP_PASSWORD und NOTION_TOKEN eintragen
export $(cat .env | xargs)
python app.py
```

App läuft dann unter `http://localhost:5000`.

## Auf GitHub veröffentlichen

```bash
cd fitness-tracker
git init
git add .
git commit -m "Initial commit: Fitness Tracker mit Notion-Integration"
git branch -M main
git remote add origin https://github.com/<dein-username>/<dein-repo>.git
git push -u origin main
```

Wichtig: `.env` steht in `.gitignore` und wird nie mitgepusht — dein Notion-Token landet
also nicht im Repo. Trotzdem empfiehlt sich ein **privates** Repository.

## Auf Render deployen

1. Gehe auf [render.com](https://render.com) und logge dich mit deinem GitHub-Account ein.
2. **New +** → **Blueprint** → wähle dein gerade gepushtes Repo aus.
   Render erkennt automatisch die `render.yaml` in diesem Projekt.
3. Render fragt dich nach folgenden Environment Variables (als "sync: false" markiert,
   damit sie nicht im Repo landen):
   - `APP_PASSWORD` — dein gewünschtes App-Login-Passwort
   - `NOTION_TOKEN` — der Token aus dem Integration-Setup oben
   `SECRET_KEY` wird automatisch generiert. Die drei `DS_*`-IDs sind bereits mit deinen
   echten Notion-Data-Source-IDs vorbelegt.
4. Klicke **Apply** — Render baut und deployed automatisch.
5. Nach ein paar Minuten ist die App unter einer URL wie
   `https://fitness-tracker-xxxx.onrender.com` erreichbar.

Im kostenlosen Render-Plan "schläft" der Service nach ca. 15 Minuten Inaktivität und
braucht beim nächsten Aufruf ein paar Sekunden zum Hochfahren — das ist normal.

### Passwort oder Token später ändern

Render Dashboard → dein Service → **Environment** → Variable bearbeiten → Service
startet automatisch neu.

## Projektstruktur

```
fitness-tracker/
├── app.py                 # Flask-App, Routen
├── notion_client_.py        # Dünner Wrapper um die Notion API (Data-Sources-Modell)
├── requirements.txt
├── render.yaml              # Render-Deployment-Konfiguration
├── templates/                # HTML-Templates (Jinja2)
└── static/
    ├── css/style.css
    └── js/charts.js          # Chart.js-Anbindung für Gewicht/Kraft-Verlauf
```

## Notion-Datenmodell (verwendet, nicht verändert außer der neuen Gewicht-DB)

**Training Sessions**: Session (Titel), Datum, Dauer (Min), Gewicht (kg) — Körpergewicht
am Trainingstag, RPE gesamt, Schlaf (Std), Ziel (Multi-Select: Oberkörper/Unterkörper/
Ganzkörper/Push/Pull/Cardio/Mobility-Reha), Notizen, Übungen (Relation)

**Trainings-Log (Übungen)**: Übung (Titel), Kategorie, Typ, Sätze, Wiederholungen,
Gewicht (kg), Satz-Details, Bewertung, Vorschlag nächstes Mal, Dauer (Min), Datum, Session (Relation)

**⚖️ Körpergewicht-Log** (neu angelegt): Datum (Titel), Gewicht (kg), Körperfett (%), Notizen

## API-Version

Nutzt Notion API Version `2025-09-03` (Data-Sources-Modell für Multi-Source-Datenbanken).
Falls Notion die API-Version künftig ändert, muss `NOTION_VERSION` in `notion_client_.py`
angepasst werden.

## Bekannte Grenzen

- Löschen ("Archivieren") in der App archiviert Notion-Seiten (`archived: true`) statt sie
  endgültig zu löschen — das entspricht Notions eigenem "in den Papierkorb verschieben".
- Freitextfelder wie "Notizen" gehen 1:1 als Plain Text nach Notion — Formatierungen,
  Kommentare oder eingebettete Inhalte aus Notion selbst werden von der App nicht angezeigt.
