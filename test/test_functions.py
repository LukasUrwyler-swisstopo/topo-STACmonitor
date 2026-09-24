"""
test_functions.py  –  Unit-Tests für die reinen Hilfsfunktionen von
api/stac_api.py und GUI_STACmonitor.py (kein Netzwerk-/GUI-Zugriff).

Aufruf:  pytest test/test_functions.py
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from api import gdwh_api as gapi
from api import stac_api as api

# Laden über importlib anhand des Dateipfads (liegt ausserhalb des Package-Baums).
_gui_path = _PROJECT_ROOT / "GUI_STACmonitor.py"
_spec = importlib.util.spec_from_file_location("gui_stac_monitor", _gui_path)
gui = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gui)


# ─── stac_api.browser_url ──────────────────────────────────────────────────

def test_browser_url_collection_int():
    url = api.browser_url("INT")
    assert url.startswith("https://sys-data.int.bgdi.ch/#/collections/")
    assert api.COLLECTION_ID in url
    assert "/items/" not in url


def test_browser_url_item_prod():
    url = api.browser_url("PROD", "kry-2025-09-19t09470000")
    assert url.startswith("https://data.geo.admin.ch/browser/index.html#/collections/")
    assert "/items/kry-2025-09-19t09470000" in url
    assert url.endswith("?.language=en")


# ─── stac_api.filter_items ─────────────────────────────────────────────────

def test_filter_items_empty_term_returns_all():
    items = [{"id": "kry-a"}, {"id": "ram-b"}]
    assert api.filter_items(items, "") == items


def test_filter_items_case_insensitive_substring():
    items = [{"id": "KRY-2025-09-19T09470000"}, {"id": "ram-2025-01-01t00000000"}]
    result = api.filter_items(items, "kry")
    assert result == [items[0]]


# ─── stac_api.stac_item_acq_date / stac_item_year ──────────────────────────

def test_acq_date_from_item_id():
    item = {"id": "kry-2025-09-19t09470000"}
    assert api.stac_item_acq_date(item) == "2025-09-19"


def test_acq_date_fallback_to_properties_datetime():
    item = {"id": "kry-ohne-datum", "properties": {"datetime": "2025-09-19T09:47:00Z"}}
    assert api.stac_item_acq_date(item) == "2025-09-19T09:47:00Z"


def test_item_year_from_item_id():
    assert api.stac_item_year({"id": "kry-2025-09-19t09470000"}) == "2025"


def test_item_year_fallback_to_properties():
    item = {"id": "kry-ohne-jahr", "properties": {"datetime": "2024-01-01T00:00:00Z"}}
    assert api.stac_item_year(item) == "2024"


def test_item_year_missing_returns_empty_string():
    assert api.stac_item_year({"id": "kry-ohne-jahr"}) == ""


# ─── stac_api.parse_asset_description / asset_area ─────────────────────────

def test_parse_asset_description_typical():
    desc = ("Area: RANDA, TerrainModel: DTM, "
             "Acquisition time: t1,t2,t3, LineId: L01,L02, Commentary: ok")
    result = api.parse_asset_description(desc)
    assert result["Area"] == "RANDA"
    assert result["TerrainModel"] == "DTM"
    # Werte mit eingebetteten Kommas dürfen nicht am Komma zerschnitten werden.
    assert result["Acquisition time"] == "t1,t2,t3"
    assert result["LineId"] == "L01,L02"
    assert result["Commentary"] == "ok"


def test_parse_asset_description_empty():
    assert api.parse_asset_description("") == {}


def test_asset_area_present():
    asset = {"description": "Area: BIRCH BLATTEN, TerrainModel: DSM"}
    assert api.asset_area(asset) == "BIRCH BLATTEN"


def test_asset_area_missing():
    assert api.asset_area({"description": "TerrainModel: DSM"}) == ""
    assert api.asset_area({}) == ""


# ─── stac_api.stac_item_area ───────────────────────────────────────────────

def test_item_area_from_properties():
    item = {"properties": {"area": "randa"}}
    assert api.stac_item_area(item) == "RANDA"


def test_item_area_fallback_to_asset_description():
    item = {
        "properties": {},
        "assets": {"nrgb.tif": {"description": "Area: Birch Blatten, TerrainModel: DSM"}},
    }
    assert api.stac_item_area(item) == "BIRCH BLATTEN"


def test_item_area_none_found():
    item = {"properties": {}, "assets": {}}
    assert api.stac_item_area(item) == ""


# ─── stac_api.build_stac_item (Extension-Deklaration / Normalisierung) ──────

_PROJ_SCHEMA = "https://stac-extensions.github.io/projection/v1.1.0/schema.json"
_FILE_SCHEMA = "https://stac-extensions.github.io/file/v2.1.0/schema.json"

# Minimal-Item im Format, das die swisstopo-STAC-API v1 liefert: Extension-
# Felder in den Assets, aber ohne "stac_extensions"-Deklaration.
def _v1_item():
    return {
        "id": "kry-2024-08-23t09110000",
        "properties": {"datetime": "2024-08-23T09:11:00Z"},
        "geometry": {"type": "Polygon",
                     "coordinates": [[[8.34, 46.68], [8.35, 46.68],
                                      [8.35, 46.69], [8.34, 46.68]]]},
        "bbox": [8.34, 46.68, 8.35, 46.69],
        "assets": {
            "a.tif": {"href": "https://example.invalid/a.tif", "gsd": 0.1,
                      "proj:epsg": 2056, "file:checksum": "1220ABCDEF"},
        },
    }


def test_build_item_declares_used_extensions():
    built = api.build_stac_item(_v1_item(), _v1_item()["assets"])
    assert built["stac_extensions"] == [_PROJ_SCHEMA, _FILE_SCHEMA]


def test_build_item_extensions_follow_stac_version():
    # stac_extensions muss laut Feldreihenfolge direkt nach stac_version stehen.
    keys = list(api.build_stac_item(_v1_item(), _v1_item()["assets"]))
    assert keys[:3] == ["type", "stac_version", "stac_extensions"]


def test_build_item_declares_only_extensions_of_selected_assets():
    # Asset ohne proj:epsg -> Projection darf nicht deklariert werden.
    item = _v1_item()
    assets = {"b.tif": {"href": "https://example.invalid/b.tif",
                        "file:checksum": "1220abcdef"}}
    assert api.build_stac_item(item, assets)["stac_extensions"] == [_FILE_SCHEMA]


def test_build_item_without_extension_fields_omits_declaration():
    # Leeres stac_extensions-Array wäre laut Spec unzulässig -> Feld entfällt.
    item = _v1_item()
    assets = {"c.tif": {"href": "https://example.invalid/c.tif", "gsd": 0.1}}
    assert "stac_extensions" not in api.build_stac_item(item, assets)


def test_build_item_keeps_extensions_declared_by_source():
    item = _v1_item()
    item["stac_extensions"] = ["https://example.invalid/custom/schema.json"]
    built = api.build_stac_item(item, item["assets"])
    assert built["stac_extensions"] == ["https://example.invalid/custom/schema.json",
                                        _PROJ_SCHEMA, _FILE_SCHEMA]


def test_build_item_lowercases_file_checksum():
    # Die API liefert den Multihash gross, die File-Extension verlangt
    # ^[a-f0-9]+$ – Hex ist case-insensitiv, der Wert bleibt also derselbe.
    item = _v1_item()
    built = api.build_stac_item(item, item["assets"])
    assert built["assets"]["a.tif"]["file:checksum"] == "1220abcdef"


def test_build_item_does_not_mutate_source_assets():
    item = _v1_item()
    api.build_stac_item(item, item["assets"])
    assert item["assets"]["a.tif"]["file:checksum"] == "1220ABCDEF"


def test_build_item_leaves_non_hex_checksum_untouched():
    item = _v1_item()
    assets = {"a.tif": {"href": "https://example.invalid/a.tif",
                        "file:checksum": "sha256:XYZ"}}
    built = api.build_stac_item(item, assets)
    assert built["assets"]["a.tif"]["file:checksum"] == "sha256:XYZ"


# ─── 0_GUI_gdwh_stac_monitor._fmt_size ─────────────────────────────────────

def test_fmt_size_none():
    assert gui._fmt_size(None) == "–"


def test_fmt_size_bytes():
    assert gui._fmt_size(512) == "512 B"


def test_fmt_size_kb():
    assert gui._fmt_size(2048) == "2.0 KB"


def test_fmt_size_mb():
    assert gui._fmt_size(5 * 1024 ** 2) == "5.0 MB"


def test_fmt_size_gb():
    assert gui._fmt_size(3 * 1024 ** 3) == "3.00 GB"


# ─── 0_GUI_gdwh_stac_monitor._fmt_date ─────────────────────────────────────

def test_fmt_date_none():
    assert gui._fmt_date(None) == "–"


def test_fmt_date_valid_http_header():
    assert gui._fmt_date("Fri, 19 Sep 2025 09:47:00 GMT") == "2025-09-19"


def test_fmt_date_unparsable_fallback():
    assert gui._fmt_date("2025-09-19-irgendwas") == "2025-09-19"


# ─── 0_GUI_gdwh_stac_monitor._status_label ─────────────────────────────────

def test_status_label_none():
    text, tag = gui._status_label(None)
    assert tag == "asset_dim"


def test_status_label_ok():
    text, tag = gui._status_label(200)
    assert "200" in text
    assert tag == "asset_ok"


def test_status_label_http_error():
    text, tag = gui._status_label(404)
    assert "404" in text
    assert tag == "asset_err"


def test_status_label_timeout():
    text, tag = gui._status_label(-2)
    assert tag == "asset_warn"


def test_status_label_other_error():
    text, tag = gui._status_label(-3)
    assert tag == "asset_warn"


# ─── 0_GUI_gdwh_stac_monitor._sync_faulty_btn ──────────────────────────────
#
# Textfarbe des Buttons "Fehlerhafte anzeigen": rot, sobald die HEAD-Prüfung
# fehlerhafte Assets gefunden hat. Getestet über einen Stub, der nur die von
# _sync_faulty_btn benötigten Attribute mitbringt – so bleibt der Test ohne
# Tk-Fenster lauffähig.

_STATUS_OK    = {"status": 200}
_STATUS_LARGE = {"status": -4}    # >50 GB, laut _asset_is_error kein Fehler
_STATUS_ERR   = {"status": 404}


class _BtnStub:
    def __init__(self):
        self.kw = {}

    def config(self, **kw):
        self.kw.update(kw)


class _FilterVarStub:
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value


class _AppStub:
    """Minimaler Ersatz für StacMonitorApp mit den echten Methoden."""

    _App = gui.StacMonitorApp
    _SHOW_ALL_BTN_LABEL    = _App._SHOW_ALL_BTN_LABEL
    _SHOW_FAULTY_BTN_LABEL = _App._SHOW_FAULTY_BTN_LABEL
    _asset_matches     = staticmethod(_App._asset_matches)
    _asset_is_error    = _App._asset_is_error
    _has_faulty_assets = _App._has_faulty_assets
    _sync_faulty_btn   = _App._sync_faulty_btn

    def __init__(self, asset_info, filter_active=False, exts=(), visible=None):
        self._asset_info = asset_info
        self._exts = list(exts)
        self._error_filter_var = _FilterVarStub(filter_active)
        self._show_faulty_btn = _BtnStub()
        self._visible_items = visible if visible is not None else [
            {"id": "it1", "assets": {"a.tif": {"href": "https://x/a.tif"},
                                     "b.laz": {"href": "https://x/b.laz"}}}]

    def _active_extensions(self):
        return self._exts

    def _active_terms(self):
        return []


def test_asset_matches_key_filter_on_key_or_filename():
    match = gui.StacMonitorApp._asset_matches
    href = "https://data.geo.admin.ch/ch.swisstopo.spezialbefliegungen/it1/ortho_nrgb_16bit.tif"
    assert match(href, "ortho.tif", [], ["16bit"])           # Treffer im Dateinamen
    assert match(href, "nrgb_ortho.tif", [], ["nrgb"])       # Treffer im Key
    assert not match(href, "ortho.tif", [], ["rgbi"])


def test_asset_matches_key_filter_ignores_url_path():
    # Collection-ID steht in jeder URL, darf aber nicht als Treffer zählen.
    href = "https://data.geo.admin.ch/ch.swisstopo.spezialbefliegungen/it1/a.tif"
    assert not gui.StacMonitorApp._asset_matches(href, "a.tif", [], ["spezialbefliegungen"])


def _btn_style(**kwargs) -> str:
    app = _AppStub(**kwargs)
    app._sync_faulty_btn()
    return app._show_faulty_btn.kw["style"]


def test_faulty_btn_neutral_before_check():
    assert _btn_style(asset_info={}) == "TButton"


def test_faulty_btn_neutral_when_all_ok():
    assert _btn_style(asset_info={"it1": {"a.tif": _STATUS_OK}}) == "TButton"


def test_faulty_btn_neutral_for_large_asset():
    # Status -4 ist das erwartete CloudFront-Verhalten, kein Fehler.
    assert _btn_style(asset_info={"it1": {"a.tif": _STATUS_LARGE}}) == "TButton"


def test_faulty_btn_red_on_error():
    assert _btn_style(asset_info={"it1": {"a.tif": _STATUS_ERR}}) == "Red.TButton"


def test_faulty_btn_amber_wins_while_filter_active():
    # Bei aktiver Fehleransicht sind die Fehler sichtbar -> kein roter Hinweis.
    assert _btn_style(asset_info={"it1": {"a.tif": _STATUS_ERR}},
                      filter_active=True) == "Amber.TButton"


def test_faulty_btn_neutral_when_error_filtered_out():
    # Fehlerhaftes .tif per Extension-Filter ausgeblendet -> der Fehler-Filter
    # würde nichts finden, also auch kein roter Hinweis.
    assert _btn_style(asset_info={"it1": {"a.tif": _STATUS_ERR}},
                      exts=[".laz"]) == "TButton"


def test_faulty_btn_red_when_error_matches_filter():
    assert _btn_style(asset_info={"it1": {"a.tif": _STATUS_ERR}},
                      exts=[".tif"]) == "Red.TButton"


def test_faulty_btn_neutral_without_visible_items():
    # Zustand direkt nach einem Reload: Ergebnisse noch da, Liste schon leer.
    assert _btn_style(asset_info={"it1": {"a.tif": _STATUS_ERR}},
                      visible=[]) == "TButton"


def test_faulty_btn_text_follows_filter_state():
    app = _AppStub(asset_info={}, filter_active=True)
    app._sync_faulty_btn()
    assert app._show_faulty_btn.kw["text"] == gui.StacMonitorApp._SHOW_ALL_BTN_LABEL
    app = _AppStub(asset_info={})
    app._sync_faulty_btn()
    assert app._show_faulty_btn.kw["text"] == gui.StacMonitorApp._SHOW_FAULTY_BTN_LABEL


# ─── 0_GUI_gdwh_stac_monitor._export_stac_browser_links ────────────────────
#
# Der Export darf ausschliesslich Item-Links enthalten; die Asset-Links sind
# Sache von "Asset-Download". Die Item-Auswahl muss zwischen beiden Exporten
# identisch bleiben.

_EXPORT_ITEMS = [
    {"id": "it-mit-laz",
     "properties": {"datetime": "2024-08-23T09:11:00Z"},
     "assets": {"a.tif": {"href": "https://x/a.tif", "description": "Area: RHONE"},
                "b.copc.laz": {"href": "https://x/b.copc.laz"}}},
    {"id": "it-nur-tif",
     "properties": {"datetime": "2015-08-05T09:23:00Z"},
     "assets": {"c.tif": {"href": "https://x/c.tif"}}},
]


class _ExportAppStub(_AppStub):
    """Stub für die Text-Exporte; erbt die Filter-Helfer von _AppStub."""

    _env_var = property(lambda self: _FilterVarStub("PROD"))
    _dark = False

    def __init__(self, exts=()):
        super().__init__(asset_info={}, exts=exts, visible=_EXPORT_ITEMS)

    def _is_checked(self, node_id):
        return True

    def _asset_is_large(self, item_id, asset_key):
        return False

    def _log_write(self, msg):
        pass


def _run_export(monkeypatch, methode, exts=()):
    """Ruft einen Export auf und gibt den erzeugten Textinhalt zurück."""
    erfasst = {}

    class _DialogStub:
        def __init__(self, parent, dark, title, content, **kw):
            erfasst["content"] = content

    monkeypatch.setattr(gui, "ExportPreviewDialog", _DialogStub)
    monkeypatch.setattr(gui, "messagebox",
                        type("M", (), {"showwarning": staticmethod(lambda *a: None),
                                       "showinfo": staticmethod(lambda *a: None)}))
    methode(_ExportAppStub(exts=exts))
    return erfasst.get("content", "")


def test_browser_export_contains_only_item_links(monkeypatch):
    content = _run_export(monkeypatch, gui.StacMonitorApp._export_stac_browser_links)
    assert "/browser/index.html#/collections/" in content
    # Kein einziger Asset-Href darf auftauchen.
    assert "https://x/" not in content
    assert "asset:" not in content


def test_browser_export_lists_every_selected_item(monkeypatch):
    content = _run_export(monkeypatch, gui.StacMonitorApp._export_stac_browser_links)
    assert content.count("item: ") == len(_EXPORT_ITEMS)


def _exported_item_ids(content):
    """Item-IDs aus einem Textexport. Vergleicht die Auswahl unabhängig davon,
    was sonst noch auf der item-Zeile steht (der Asset-Export hängt dort den
    STAC-Browser-Link an)."""
    return [z[len("item: "):].split(";")[0]
            for z in content.splitlines() if z.startswith("item: ")]


def test_browser_and_download_export_select_same_items(monkeypatch):
    # Der .laz-Filter lässt nur das erste Item übrig – in beiden Exporten.
    browser = _run_export(monkeypatch, gui.StacMonitorApp._export_stac_browser_links,
                          exts=[".laz"])
    download = _run_export(monkeypatch, gui.StacMonitorApp._create_download_links,
                           exts=[".laz"])
    assert _exported_item_ids(browser) == _exported_item_ids(download) == ["it-mit-laz"]


def test_download_export_still_contains_asset_links(monkeypatch):
    # Gegenprobe: der Asset-Export darf die Hrefs nicht verloren haben.
    content = _run_export(monkeypatch, gui.StacMonitorApp._create_download_links)
    assert "https://x/a.tif" in content


def test_download_export_item_line_carries_browser_link(monkeypatch):
    # Die item-Zeile trägt den STAC-Browser-Link direkt hinter dem Semikolon.
    content = _run_export(monkeypatch, gui.StacMonitorApp._create_download_links)
    item_zeilen = [z for z in content.splitlines() if z.startswith("item: ")]
    assert item_zeilen, "keine item-Zeile im Export"
    for zeile in item_zeilen:
        iid = zeile[len("item: "):].split(";")[0]
        assert zeile == f"item: {iid}; {api.browser_url('PROD', iid, include_lang=False)}"


# ─── gdwh_api._parse_custom_attributes (Auftragstyp/Area/Jahr-Extraktion) ──
# Speist die im GDWH-Tab neu angezeigten Spalten "Auftragstyp" und "GDS-Key".

def test_parse_custom_attributes_extracts_auftragstyp():
    xml = "<auftragstyp>RAM</auftragstyp><area>RANDA</area>"
    result = gapi._parse_custom_attributes(xml)
    assert result["auftragstyp"] == "RAM"
    assert result["area"] == "RANDA"


def test_parse_custom_attributes_accepts_alternate_tag_names():
    xml = "<orderType>ADS</orderType>"
    assert gapi._parse_custom_attributes(xml)["auftragstyp"] == "ADS"


def test_parse_custom_attributes_empty_fragment():
    result = gapi._parse_custom_attributes("")
    assert result == {"area": "", "line_id": "", "commentary": "",
                       "auftragstyp": "", "stac_datetime": ""}


def test_parse_custom_attributes_unparsable_fragment():
    result = gapi._parse_custom_attributes("<not-closed>")
    assert result["auftragstyp"] == ""


# ─── gdwh_api.gdwh_index_file_metadata_by_import ───────────────────────────

def test_index_file_metadata_by_import_maps_auftragstyp():
    file_metadata = [{
        "importUuid": "uuid-1",
        "customAttributes": "<auftragstyp>RAM</auftragstyp><area>RANDA</area>",
        "temporalKey": 2024,
    }]
    index = gapi.gdwh_index_file_metadata_by_import(file_metadata)
    assert index["uuid-1"]["auftragstyp"] == "RAM"
    assert index["uuid-1"]["area"] == "RANDA"
    assert index["uuid-1"]["year"] == "2024"


def test_index_file_metadata_by_import_first_match_wins():
    file_metadata = [
        {"importUuid": "uuid-1", "customAttributes": "<auftragstyp>RAM</auftragstyp>"},
        {"importUuid": "uuid-1", "customAttributes": "<auftragstyp>ADS</auftragstyp>"},
    ]
    index = gapi.gdwh_index_file_metadata_by_import(file_metadata)
    assert index["uuid-1"]["auftragstyp"] == "RAM"


def test_index_file_metadata_by_import_skips_missing_uuid():
    file_metadata = [{"customAttributes": "<auftragstyp>RAM</auftragstyp>"}]
    assert gapi.gdwh_index_file_metadata_by_import(file_metadata) == {}


# ─── gdwh_api.gdwh_import_id / gdwh_import_date ────────────────────────────

def test_gdwh_import_id_prefers_uuid():
    assert gapi.gdwh_import_id({"uuid": "abc", "id": "other"}) == "abc"


def test_gdwh_import_id_missing_returns_placeholder():
    assert gapi.gdwh_import_id({}) == "?"


def test_gdwh_import_date_truncates_and_replaces_t():
    imp = {"importDate": "2024-05-01T12:34:56.789Z"}
    assert gapi.gdwh_import_date(imp) == "2024-05-01 12:34"


def test_gdwh_import_date_missing_returns_placeholder():
    assert gapi.gdwh_import_date({}) == "–"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
