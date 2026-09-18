"""
Tests fuer config.py: Pfade, Stunden-Format, settings.json und Speicherort.

Ausfuehren wie test_generator.py (siehe dort).
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import make_png
from lerntagebuch import config


class TestPfade(unittest.TestCase):
    """Portabilitaet: alle Pfade haengen am App-Ordner, nicht am Arbeitsverzeichnis."""

    def test_pfade_absolut_und_im_app_ordner(self):
        for pfad in (config.TEMPLATE_PATH, config.WEEK_PATH,
                     config.OUTPUT_DIR, config.SETTINGS_PATH):
            with self.subTest(pfad=pfad):
                self.assertTrue(pfad.is_absolute())
                self.assertTrue(pfad.is_relative_to(config.APP_DIR))

    def test_vorlage_vorhanden(self):
        self.assertTrue(config.TEMPLATE_PATH.is_file())

    def test_als_exe_nutzerdaten_neben_der_exe(self):
        # PyInstaller setzt sys.frozen und sys._MEIPASS. Nutzerdaten gehoeren
        # neben die .exe, die Vorlage kommt aus dem Bundle.
        exe = Path(tempfile.gettempdir()) / "Lerntagebuch" / "Lerntagebuch.exe"
        bundle = exe.parent / "_internal"
        with mock.patch.object(sys, "frozen", True, create=True), \
                mock.patch.object(sys, "_MEIPASS", str(bundle), create=True), \
                mock.patch.object(sys, "executable", str(exe)):
            app_dir, bundle_dir = config.app_dirs()
        self.assertEqual(app_dir, exe.parent.resolve())
        self.assertEqual(bundle_dir, bundle)

    def test_aus_dem_quellcode_alles_im_projektordner(self):
        app_dir, bundle_dir = config.app_dirs()
        self.assertEqual(app_dir, bundle_dir)
        self.assertTrue((app_dir / "lerntagebuch" / "config.py").is_file())


class TestStunden(unittest.TestCase):

    def test_parse_komma_und_punkt(self):
        self.assertEqual(config.parse_hours("8,5"), 8.5)
        self.assertEqual(config.parse_hours("8.5"), 8.5)
        self.assertEqual(config.parse_hours(" 7 "), 7)
        self.assertEqual(config.parse_hours(10), 10)
        self.assertEqual(config.parse_hours(0), 0)
        self.assertEqual(config.parse_hours(24), 24)

    def test_parse_ungueltig(self):
        for wert in ("", "  ", "abc", "8,5,5", "-1", "24,5", "nan", "inf", True, None):
            with self.subTest(wert=wert):
                with self.assertRaises((ValueError, TypeError)):
                    config.parse_hours(wert)

    def test_format(self):
        self.assertEqual(config.format_hours(10), "10")
        self.assertEqual(config.format_hours(10.0), "10")
        self.assertEqual(config.format_hours(8.5), "8,5")
        self.assertEqual(config.format_hours(7.25), "7,25")
        self.assertEqual(config.format_hours(0), "0")

    def test_standard_entspricht_altem_verhalten(self):
        # Vor Schritt 3 fest im Code: S/M 10 (Fr 7), B 8,5 (Fr 6), F/U 0
        h = config.DEFAULT_HOURS
        self.assertEqual(h["S"], [10, 10, 10, 10, 7])
        self.assertEqual(h["M"], [10, 10, 10, 10, 7])
        self.assertEqual(h["B"], [8.5, 8.5, 8.5, 8.5, 6])
        self.assertEqual(h["F"], [0] * 5)
        self.assertEqual(h["U"], [0] * 5)

    def test_standard_ist_kopie(self):
        a = config.default_settings()
        a["hours"]["S"][0] = 99
        self.assertEqual(config.default_settings()["hours"]["S"][0], 10)
        self.assertEqual(config.DEFAULT_HOURS["S"][0], 10)


class TestSettingsDatei(unittest.TestCase):

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp())
        self.path = self._tmp / "settings.json"

    def tearDown(self):
        shutil.rmtree(self._tmp)

    def write(self, content):
        self.path.write_text(content, encoding="utf-8")

    def test_fehlt_ergibt_standard_ohne_warnung(self):
        settings, warnings = config.load_settings(self.path)
        self.assertEqual(settings, config.default_settings())
        self.assertEqual(warnings, [])

    def test_speichern_und_laden(self):
        s = config.default_settings()
        s.update(last_name="Mustermann", first_name="Max")
        s["hours"]["B"] = [8, 8, 8, 8, 5.5]
        s["default_pattern"] = "BBBBB"
        s["default_lf"] = "5, 7"
        s["output_dir"] = "Abgaben"
        config.save_settings(s, self.path)
        geladen, warnings = config.load_settings(self.path)
        self.assertEqual(geladen, s)
        self.assertEqual(warnings, [])
        self.assertFalse(self.path.with_name("settings.json.tmp").exists())

    def test_umlaute(self):
        s = config.default_settings()
        s.update(last_name="Müller-Lüdenscheidt", first_name="Jürgen")
        config.save_settings(s, self.path)
        self.assertEqual(config.load_settings(self.path)[0], s)

    def test_teilweise_datei_wird_ergaenzt(self):
        self.write('{"last_name": "Mustermann", "first_name": "Max"}')
        settings, warnings = config.load_settings(self.path)
        self.assertEqual(config.full_name(settings), "Mustermann, Max")
        self.assertEqual(settings["hours"], config.DEFAULT_HOURS)
        self.assertEqual(settings["default_pattern"], "MSSSM")
        self.assertEqual(warnings, [])

    def test_kaputtes_json(self):
        self.write("{ das ist kein json")
        settings, warnings = config.load_settings(self.path)
        self.assertEqual(settings, config.default_settings())
        self.assertEqual(len(warnings), 1)

    def test_falscher_typ(self):
        self.write("[1, 2, 3]")
        settings, warnings = config.load_settings(self.path)
        self.assertEqual(settings, config.default_settings())
        self.assertEqual(len(warnings), 1)

    def test_ungueltige_werte_einzeln_ersetzt(self):
        self.write(json.dumps({
            "last_name": "",
            "hours": {"S": [10, 10, "abc", 10, 7],   # ungueltig
                      "B": [8, 8, 8, 8],              # nur 4 Werte
                      "M": [9, 9, 9, 9, 6]},          # gueltig
            "default_pattern": "XYZ",
        }))
        settings, warnings = config.load_settings(self.path)
        self.assertEqual(settings["last_name"], config.DEFAULT_LAST_NAME)
        self.assertEqual(settings["hours"]["S"], config.DEFAULT_HOURS["S"])
        self.assertEqual(settings["hours"]["B"], config.DEFAULT_HOURS["B"])
        self.assertEqual(settings["hours"]["M"], [9, 9, 9, 9, 6])
        self.assertEqual(settings["default_pattern"], "MSSSM")
        self.assertEqual(len(warnings), 4)

    def test_bom(self):
        self.path.write_text('{"last_name": "Mit BOM"}', encoding="utf-8-sig")
        self.assertEqual(config.load_settings(self.path)[0]["last_name"], "Mit BOM")

    def test_alter_name_wird_aufgeteilt(self):
        # settings.json aus aelteren Versionen: nur "name" als "Nachname, Vorname"
        self.write('{"name": "Mustermann, Max"}')
        settings, warnings = config.load_settings(self.path)
        self.assertEqual((settings["last_name"], settings["first_name"]),
                         ("Mustermann", "Max"))
        self.assertNotIn("name", settings)
        self.assertEqual(warnings, [])

    def test_neue_felder_gehen_vor(self):
        self.write('{"name": "Alt, Name", "last_name": "Neu", "first_name": "Max"}')
        settings, _ = config.load_settings(self.path)
        self.assertEqual(config.full_name(settings), "Neu, Max")


class TestSpeicherort(unittest.TestCase):

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self._tmp)

    def test_standard(self):
        self.assertEqual(config.resolve_output_dir({"output_dir": ""}),
                         (config.OUTPUT_DIR, False))

    def test_eigener_ordner(self):
        self.assertEqual(config.resolve_output_dir({"output_dir": str(self._tmp)}),
                         (self._tmp, False))

    def test_fallback_wenn_ordner_fehlt(self):
        fehlt = str(self._tmp / "gibt_es_nicht")
        self.assertEqual(config.resolve_output_dir({"output_dir": fehlt}),
                         (config.OUTPUT_DIR, True))

    def test_relativer_pfad_gilt_ab_app_ordner(self):
        # "resources" existiert im App-Ordner, egal wo die App liegt
        self.assertEqual(config.resolve_output_dir({"output_dir": "resources"}),
                         (config.APP_DIR / "resources", False))

    def test_portable_path(self):
        innen = config.APP_DIR / "resources"
        self.assertEqual(config.portable_path(innen), "resources")
        self.assertEqual(config.portable_path(self._tmp), str(self._tmp.resolve()))


class TestUnterschrift(unittest.TestCase):

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp())
        self.png = self._tmp / "meine_unterschrift.PNG"
        self.png.write_bytes(make_png(40, 20))

    def tearDown(self):
        shutil.rmtree(self._tmp)

    def test_keine(self):
        self.assertEqual(config.resolve_signature({"signature": ""}), (None, False))

    def test_vorhanden(self):
        self.assertEqual(config.resolve_signature({"signature": str(self.png)}),
                         (self.png, False))

    def test_fehlt(self):
        fehlt = str(self._tmp / "weg.png")
        self.assertEqual(config.resolve_signature({"signature": fehlt}), (None, True))

    def test_standard_ohne_unterschrift(self):
        self.assertEqual(config.default_settings()["signature"], "")
        self.assertFalse(config.default_settings()["signature_name"])

    def test_nachname_als_unterschrift(self):
        s = {"last_name": "Mustermann", "first_name": "Max", "signature_name": True}
        self.assertEqual(config.signature_text(s), "Mustermann")
        s["signature_name"] = False
        self.assertEqual(config.signature_text(s), "")

    def test_nachname_option_aus_settings_json(self):
        path = self._tmp / "settings.json"
        path.write_text(json.dumps({"signature_name": True}), encoding="utf-8")
        self.assertTrue(config.load_settings(path)[0]["signature_name"])
        path.write_text(json.dumps({"signature_name": "ja"}), encoding="utf-8")
        self.assertFalse(config.load_settings(path)[0]["signature_name"])  # kein bool

    def test_pruefung(self):
        self.assertIsNone(config.check_signature_image(self.png))
        falsche_endung = self._tmp / "x.gif"
        falsche_endung.write_bytes(b"GIF89a")
        self.assertIsNotNone(config.check_signature_image(falsche_endung))
        kaputt = self._tmp / "kaputt.png"
        kaputt.write_bytes(b"kein bild")
        self.assertIsNotNone(config.check_signature_image(kaputt))

    def test_kopieren_in_app_ordner(self):
        ziel = self._tmp / "app"
        ziel.mkdir()
        name = config.store_signature(self.png, ziel)
        self.assertEqual(name, "unterschrift.png")  # Endung klein
        self.assertEqual((ziel / name).read_bytes(), self.png.read_bytes())

    def test_ersetzt_alte_andere_endung(self):
        ziel = self._tmp / "app"
        ziel.mkdir()
        (ziel / "unterschrift.jpg").write_bytes(b"alt")
        config.store_signature(self.png, ziel)
        self.assertEqual(sorted(p.name for p in ziel.iterdir()), ["unterschrift.png"])

    def test_quelle_ist_schon_die_kopie(self):
        ziel = self._tmp / "app"
        ziel.mkdir()
        name = config.store_signature(self.png, ziel)
        config.store_signature(ziel / name, ziel)  # darf sich nicht selbst loeschen
        self.assertEqual((ziel / name).read_bytes(), self.png.read_bytes())

    def test_entfernen(self):
        ziel = self._tmp / "app"
        ziel.mkdir()
        config.store_signature(self.png, ziel)
        config.remove_signature(ziel)
        config.remove_signature(ziel)  # zweimal ist kein Fehler
        self.assertEqual(list(ziel.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
