# STAC Monitor – ch.swisstopo.spezialbefliegungen

GUI-Tool zur Überwachung der **STAC-Collection**
`ch.swisstopo.spezialbefliegungen` auf INT- und PROD-Umgebung von swisstopo /
BGDI, sowie DataPackages im **Geodata-Warehouse (GDWH)**.
Read-only-GUI.

Angebunden ist die **STAC-API v1** (`.../api/stac/v1/`, liefert
`stac_version: 1.0.0`). Der Vorgänger `v0.9` antwortet noch, ist aber
abgekündigt – die Endpunkte stehen in `ENVIRONMENTS` in `api/stac_api.py`.

## Schnellstart

1. **Einmalig:** Für den STAC-Tab braucht das Script den `secrets/`-Ordner mit
   den entsprechenden .json-Dateien (Zugangsdaten). Diese müssen vom
   Benutzer bei TBKN/swisstopo angefragt werden, siehe
   [Einrichtung](#einrichtung)
2. Tool starten: WIN-Taste + cmd (Terminal starten):

   ```bash
   python pfad/GUI_monitoring_stac_gdwh.py
   ```
<img width="896" height="674" alt="image" src="https://github.com/user-attachments/assets/fb37c46d-62e8-4f25-89f2-e7c305c7beca" />



### Tab STAC

3. Im GUI oben: **Umgebung** (INT/PROD) wählen und **Credentials laden**
4. Optional Filter setzen (Auftragstyp, Jahr, Suchbegriff, Dateiendung),
   dann **Laden** klicken
5. In der Baumansicht die gewünschten Items/Assets per Checkbox auswählen
   (oder **Alle auswählen**)
6. Im Bereich **STAC-Funktionen**: **Assets prüfen (HEAD)** für Status &
   Grösse, danach je nach Bedarf herunterladen oder exportieren
7. Asset **GUI-Viewer**: einzeln ausgewählte Assets (ausser 16bit und copc) direkt in map.geo.admin.ch anzeigen, wahlweise im Browser oder in einem angedockten Viewer-Fenster

### Tab GDWH

1. **Umgebung** (INT/PROD) wählen – Authentifizierung läuft automatisch über
   die aktuelle Windows-Session (kein Credentials-Schritt nötig)
2. **GDS-Key** wählen (`SB_DOP`, `SB_DOP_16`, `SB_DSM`, `SB_DSM_PUNKTWOLKE`,
   oder **Alle GDS-Keys** für alle vier zusammen – die GDWH-API kennt keinen
   eigenen "Alle"-Endpunkt, das Tool fragt die Keys dafür nacheinander ab),
   optional **Jahr** eintragen, dann **Imports laden**
3. Die Liste zeigt pro DataPackage Jahr, Auftragstyp, Area, StacItemDatetime,
   einen Status sowie (rechts, nach Status) den GDS-Key des Imports:
   - **✓ OK** – FileMetadata-Match vorhanden, Area und StacItemDatetime
     gesetzt
   - **⚠ unvollständig** – FileMetadata-Match vorhanden, aber Area oder
     StacItemDatetime fehlt
   - **⚠ Kein FileMetadata-Match** – zu diesem Import existiert kein
     FileMetadata-Eintrag; deutet auf einen unsauberen GDWH-Zustand hin
     (z.B. eine frühere, unvollständige Löschung)

   Der Jahresfilter, der **Auftragstyp**-Dropdown (`Alle` / `RAM` / `KRY`)
   sowie das **Area**-Textfeld (optional; filtert als Teilstring-Suche,
   z.B. `ALETSCH` findet auch `ALETSCH_MOOSFLUE`; leer = alle Areas)
   filtern die bereits geladene Liste sofort weiter, ohne Neu-Laden. Mit
   **Nur Fehlerhafte anzeigen** blendet die Liste auf die beiden ⚠-Status
   ein, statt durch alle DataPackages scrollen zu müssen; ein zweiter
   Klick (**Alle DataPackages anzeigen**) hebt den Filter wieder auf. Alle
   Filter lassen sich kombinieren.

## Funktionen

- **Items laden & filtern** – ganze Collection oder gezielt per Item-ID;
  Filter nach Auftragstyp, Jahr, Suchbegriff, Dateiendung
- **Auswahl per Checkbox** – einzelne Assets oder ganze Items, inkl.
  "Alle auswählen" / "Alles abwählen"
- **Assets prüfen (HEAD)** – prüft Status, Dateigrösse und Änderungsdatum
  der ausgewählten Assets. Assets über 50 GB (von CloudFront normalerweise
  mit Fehler 400 gemeldet) werden korrekt als ✓ **>50GB** statt als Fehler
  erkannt
- **Fehlerhafte anzeigen** / **ITEMs ohne Thumbnail** / **ITEMs only with
  Thumbnail** – blenden die Baumansicht gezielt auf problematische bzw.
  unvollständige Items ein, bzw. auf Items, die nur aus einem Thumbnail
  ohne echte Nutzdaten bestehen. **Fehlerhafte anzeigen** wird nach der
  HEAD-Prüfung **rot**, falls es unter den aktuellen Filtereinstellungen
  fehlerhafte Assets gibt – ohne Fehler bleibt die Schrift neutral
- Gruppe **Export Links** – erzeugt Textdateien zur Auswahl, jeweils mit
  Vorschau vor dem Speichern:
  - **STAC-Browser** – ausschliesslich die STAC-Browser-Links der Items
    (TXT), inkl. Jahr und Area als Info-Zeile. Bewusst ohne Asset-Links;
    die Item-Auswahl ist dieselbe wie bei **Asset-Download**
  - **STAC-Item** – die Auswahl als valide STAC-1.0.0-ItemCollection
    (GeoJSON FeatureCollection), also maschinenlesbar für pystac, GDAL/OGR
    (STACIT) oder QGIS – inkl. der von der API nicht mitgelieferten
    `stac_extensions`-Deklaration
  - **Asset-Download** – Download-Links der Auswahl zum Weitergeben an
    Kunden, je Item zusätzlich der STAC-Browser-Link auf der `item`-Zeile;
    bei Assets über 50 GB inkl. Hinweis auf die nötige Download-Methode
- Gruppe **direkter Download** → **Download Assets** – lädt die ausgewählten
  Assets direkt auf die eigene Festplatte (ein Unterordner pro Item). Assets
  über 50 GB werden automatisch in Teilstücken heruntergeladen, da sie sonst
  am CloudFront-Limit scheitern würden
- **Kartenviewer** – ausgewählte GeoTIFFs bzw. Tagesübersichten direkt in
  map.geo.admin.ch anzeigen, wahlweise im Browser oder in einem
  angedockten Viewer-Fenster
- Statistik (OK/Fehler/Gesamtgrösse), Item-JSON-Detailansicht,
  Hell/Dark-Theme
- **Tab GDWH** – Liste der DataPackages je GDS-Key (einzeln oder für alle
  GDS-Keys zusammen) mit Jahr/Auftragstyp/Area/StacItemDatetime,
  Validitäts-Status und GDS-Key, inkl. Filter auf nur fehlerhafte
  DataPackages (siehe [Tab GDWH](#tab-gdwh))

## Voraussetzungen

- Python 3.11+ mit Tkinter (in der Standard-Windows-Installation enthalten)
- Paket `requests` (`pip install requests`)
- Für das angedockte Viewer-Fenster: Google Chrome oder Microsoft Edge.
  Das Paket `pywin32` wird beim ersten Start bei Bedarf automatisch
  nachinstalliert
- Für den GDWH-Tab: Paket `requests-negotiate-sspi` (wird beim ersten Start
  bei Bedarf automatisch nachinstalliert). Authentifizierung läuft über
  Windows SSPI mit dem aktuell eingeloggten User – keine separaten
  Zugangsdaten nötig, GDWH ist nur im internen Netz / VPN erreichbar

## Einrichtung

Zugangsdaten für den STAC-Tab hinterlegen unter `secrets/stac_credentials.json`:

```json
{
  "INT":  {"username": "...", "password": "..."},
  "PROD": {"username": "...", "password": "..."}
}
```

Optional: `secrets/proxy_config.json` anpassen, falls ein anderer
Firmenproxy als `proxy-bvcol.admin.ch:8080` verwendet wird. Der Ordner
`secrets/` ist in `.gitignore` ausgeschlossen und wird nicht versioniert.

Im Bundesnetz läuft der Zugriff automatisch über diesen Proxy; ausserhalb
(z.B. privater Rechner) schaltet das Tool selbstständig auf eine
Direktverbindung um. Der GDWH-Tab braucht keine Zugangsdaten (Windows-SSPI)
und verbindet sich direkt, ohne Proxy.

## Dateien

| Datei | Zweck |
|---|---|
| `GUI_monitoring_stac_gdwh.py` | GUI-Anwendung (Tkinter) |
| `api/stac_api.py` | STAC-API-Hilfsfunktionen (inkl. Download) |
| `api/gdwh_api.py` | GDWH-API-Hilfsfunktionen (read-only) |
| `test/test_functions.py` | Unit-Tests (pytest) |
| `secrets/stac_credentials.json` | Zugangsdaten INT/PROD (nicht versioniert) |
| `secrets/proxy_config.json` | Proxy-Konfiguration (nicht versioniert) |
