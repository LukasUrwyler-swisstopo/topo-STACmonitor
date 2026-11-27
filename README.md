# STAC Monitor – ch.swisstopo.spezialbefliegungen

GUI-Tool zur Überwachung der **STAC-Collection**
`ch.swisstopo.spezialbefliegungen` auf INT- und PROD-Umgebung von swisstopo /
BGDI. Read-only-GUI.

Angebunden ist die **STAC-API v1** (`.../api/stac/v1/`, liefert
`stac_version: 1.0.0`). Der Vorgänger `v0.9` antwortet noch, ist aber
abgekündigt – die Endpunkte stehen in `ENVIRONMENTS` in `api/stac_api.py`.

## Schnellstart

1. **Kein Login nötig:** Die STAC-API ist für Lesezugriffe öffentlich. Optional
   lässt sich der Firmenproxy im Ordner `proxys/` anpassen, siehe
   [Einrichtung](#einrichtung)
2. Tool starten: WIN-Taste + cmd (Terminal starten):

   ```bash
   python pfad/GUI_STACmonitor.py
   ```
<img width="968" height="911" alt="image" src="https://github.com/user-attachments/assets/f8de60b2-cb5e-4d97-b75c-1a9ef1808aec" />


### Tab STAC

3. Im GUI oben (Abschnitt 1): **Umgebung** wählen (Default PROD)
4. Optional Filter setzen (Auftragstyp, Jahr, Area, Item-ID, Asset-Key,
   Dateiendung tif/laz/jpg/kml/txt),
   dann in Abschnitt 1 **ITEM-Liste laden** klicken (daneben:
   **STAC Browser öffnen**)
5. In der Baumansicht die gewünschten Items/Assets per Checkbox auswählen
   (oder **Alles auswählen**)
6. Im Bereich **STAC-Funktionen** (Details siehe
   [STAC-Funktionen](#stac-funktionen-button-leiste-unter-der-baumansicht)):
   - **Quality Check**: **Assets prüfen (HEAD)** für Status & Grösse,
     danach optional filtern (**Fehlerhafte anzeigen**, **ITEMs ohne
     Thumbnail**, **ITEMs only with Thumbnail**, **Assets ohne Description**)
   - **Export Links**: **STAC-Browser**, **STAC-JSON** oder
     **Asset-Download** (bzw. **Asset-href-Links**) als Datei exportieren
   - **direkter Download**: **Download Assets** auf die eigene Festplatte
7. **ASSET Viewer**: einzeln ausgewählte Assets (ausser 16bit und copc) direkt in map.geo.admin.ch anzeigen, wahlweise im Browser oder in einem angedockten Viewer-Fenster

## Funktionen

### Tab STAC – Laden & Auswahl

- **Items laden & filtern** – ganze Collection oder gezielt per Item-ID;
  Filter nach Auftragstyp, Jahr, Area, Item-ID, Asset-Key (Teilstring im
  Key oder Dateinamen, z.B. `nrgb`, `16bit`) und Dateiendung
  (tif, copc.laz/laz, jpg, kml, txt)
- **Auswahl per Checkbox** – einzelne Assets oder ganze Items, inkl.
  **Alles auswählen** / **Alles abwählen**

### STAC-Funktionen (Button-Leiste unter der Baumansicht)

- Gruppe **Quality Check**:
  - **Assets prüfen (HEAD)** – prüft Status, Dateigrösse und
    Änderungsdatum der ausgewählten Assets. Assets über 50 GB (von
    CloudFront normalerweise mit Fehler 400 gemeldet) werden korrekt als
    ✓ **>50GB** statt als Fehler erkannt
  - **Fehlerhafte anzeigen** – blendet die Baumansicht auf Assets mit
    Fehlerstatus ein. Wird nach der HEAD-Prüfung **rot**, falls es unter
    den aktuellen Filtereinstellungen fehlerhafte Assets gibt – ohne Fehler
    bleibt die Schrift neutral
  - **ITEMs ohne Thumbnail** – nur bei Auftragstyp RAM sichtbar
    (Thumbnail-Pflicht); zeigt Items ohne Thumbnail-Asset
  - **ITEMs only with Thumbnail** – zeigt Items, die genau ein Asset
    besitzen und dieses ein Thumbnail ist (also ohne echte Nutzdaten)
  - **Assets ohne Description** – zeigt Assets ohne bzw. mit leerer
    `description` (Thumbnails ausgenommen). Solange aktiv, wird der
    Export-Button **Asset-Download** zu **Asset-href-Links** (siehe unten)

  Alle Filter-Buttons sind Toggles: aktiv **amber** beschriftet mit **Alle
  Assets wieder anzeigen**, ein zweiter Klick hebt den Filter auf. Sie
  lassen sich untereinander und mit den Filtern oben kombinieren; beim
  Umschalten wird die Auswahl zurückgesetzt
- Gruppe **Export Links** – erzeugt Textdateien zur Auswahl, jeweils mit
  Vorschau vor dem Speichern:
  - **STAC-Browser** – ausschliesslich die STAC-Browser-Links der Items
    (TXT), inkl. Jahr und Area als Info-Zeile. Bewusst ohne Asset-Links;
    die Item-Auswahl ist dieselbe wie bei **Asset-Download**
  - **STAC-JSON** – die Auswahl als valide STAC-1.0.0-ItemCollection
    (GeoJSON FeatureCollection), also maschinenlesbar für pystac, GDAL/OGR
    (STACIT) oder QGIS – inkl. der von der API nicht mitgelieferten
    `stac_extensions`-Deklaration
  - **Asset-Download** – Download-Links der Auswahl zum Weitergeben an
    Kunden, je Item zusätzlich der STAC-Browser-Link auf der `item`-Zeile;
    bei Assets über 50 GB inkl. Hinweis auf die nötige Download-Methode.
    Bei aktivem **Assets ohne Description** heisst der Button
    **Asset-href-Links** und exportiert eine reine href-Liste (Eingabe für
    topo-STACassetEditor); er wird **grün**, sobald Assets gelistet sind
- Gruppe **direkter Download** → **Download Assets** – lädt die ausgewählten
  Assets direkt auf die eigene Festplatte (ein Unterordner pro Item). Assets
  über 50 GB werden automatisch in Teilstücken heruntergeladen, da sie sonst
  am CloudFront-Limit scheitern würden
- Gruppe **ASSET Viewer** – ausgewählte GeoTIFFs bzw. Tagesübersichten
  direkt in map.geo.admin.ch anzeigen:
  - **Link auf Kartenviewer** – öffnet die Ansicht im Browser
  - **GUI Viewer öffnen** – öffnet sie in einem angedockten Viewer-Fenster

### Weitere Funktionen

- Statistik (OK/Fehler/Gesamtgrösse), Item-JSON-Detailansicht,
  Hell/Dark-Theme

## Voraussetzungen

- Python 3.11+ mit Tkinter (in der Standard-Windows-Installation enthalten)
- Paket `requests` (`pip install requests`)
- Für das angedockte Viewer-Fenster: Google Chrome oder Microsoft Edge.
  Das Paket `pywin32` wird beim ersten Start bei Bedarf automatisch
  nachinstalliert

## Einrichtung

Zugangsdaten braucht der Monitor keine: Er liest nur (GET/HEAD), und die
STAC-API von swisstopo/BGDI ist für Lesezugriffe öffentlich.

Optional: Für einen anderen Firmenproxy als `proxy-bvcol.admin.ch:8080` die
Vorlage `proxys/proxy_config.example.json` nach `proxys/proxy_config.json`
kopieren und anpassen. Verwendet wird der erste Eintrag unter `proxies` mit
`"enabled": true`. Fehlt die Datei, gilt `proxy-bvcol.admin.ch:8080`.
Nur `proxy_config.json` ist in `.gitignore` ausgeschlossen, damit lokale
Anpassungen (z.B. Zugangsdaten in der Proxy-URL) nicht ins Repo gelangen.

Im Bundesnetz läuft der Zugriff automatisch über diesen Proxy; ausserhalb
(z.B. privater Rechner) schaltet das Tool selbstständig auf eine
Direktverbindung um.

## Dateien

| Datei | Zweck |
|---|---|
| `GUI_STACmonitor.py` | GUI-Anwendung (Tkinter) |
| `api/stac_api.py` | STAC-API-Hilfsfunktionen (inkl. Download) |
| `test/test_functions.py` | Unit-Tests (pytest) |
| `proxys/proxy_config.example.json` | Vorlage für die Proxy-Konfiguration |
| `proxys/proxy_config.json` | Lokale Proxy-Konfiguration, optional (nicht versioniert) |
