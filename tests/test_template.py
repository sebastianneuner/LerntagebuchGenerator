"""
Tests fuer resources/template.docx.

Sichern ab, dass das Template keine persoenlichen Daten enthaelt (es liegt in
einem oeffentlichen Repo) und dass der Unterschrift-Platzhalter vorhanden ist.
"""

import re
import unittest
import zipfile
from pathlib import Path

from docx import Document

from lerntagebuch import config
from lerntagebuch.generator import NS


SPERRLISTE = Path(__file__).with_name("sperrliste.txt")


def sperrliste():
    """Woerter, die nirgends im Template stehen duerfen.

    Die Namen selbst sollen nicht im (oeffentlichen) Repo stehen. Sie kommen
    deshalb aus der lokalen, gitignorierten tests/sperrliste.txt (ein Wort je
    Zeile, # fuer Kommentare) und aus Nach- und Vorname in settings.json.
    """
    woerter = set()
    if SPERRLISTE.is_file():
        for zeile in SPERRLISTE.read_text(encoding="utf-8-sig").splitlines():
            zeile = zeile.strip()
            if zeile and not zeile.startswith("#"):
                woerter.add(zeile)
    settings, _ = config.load_settings()
    if settings["last_name"] != config.DEFAULT_LAST_NAME:
        woerter.add(settings["last_name"])
    if settings["first_name"] != config.DEFAULT_FIRST_NAME:
        woerter.add(settings["first_name"])
    return sorted(woerter)


class TestTemplate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.zip = zipfile.ZipFile(config.TEMPLATE_PATH)
        cls.doc = Document(str(config.TEMPLATE_PATH))

    @classmethod
    def tearDownClass(cls):
        cls.zip.close()

    def test_metadaten_ohne_personen(self):
        cp = self.doc.core_properties
        self.assertEqual(cp.author, "")
        self.assertEqual(cp.last_modified_by, "")

    def test_nur_platzhalterbild_enthalten(self):
        media = [n for n in self.zip.namelist() if n.startswith("word/media/")]
        self.assertEqual(len(media), 1, media)
        # Transparentes Platzhalterbild ist winzig, ein Scan waere viel groesser
        self.assertLess(self.zip.getinfo(media[0]).file_size, 1000)

    def test_keine_persoenlichen_angaben(self):
        # Mailadressen und persoenliche Namen duerfen nirgends stehen, auch
        # nicht in Metadaten oder Alternativtexten.
        alles = "".join(self.zip.read(n).decode("utf-8", "replace")
                        for n in self.zip.namelist()
                        if n.endswith(".xml") or n.endswith(".rels"))
        self.assertEqual(re.findall(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", alles), [])
        for wort in sperrliste():
            with self.subTest(wort=wort):
                self.assertNotIn(wort, alles)

    def test_unterschrift_platzhalter(self):
        prs = [pr for pr in self.doc.element.body.iter(f"{{{NS['wp']}}}docPr")
               if pr.get("descr") == config.SIGNATURE_PLACEHOLDER]
        self.assertEqual(len(prs), 1)
        frame = prs[0].getparent()
        self.assertEqual(frame.findall(f".//{{{NS['a']}}}srcRect"), [])
        self.assertIsNotNone(frame.find(f".//{{{NS['a']}}}blip"))

    def test_tages_tabellen_gleich_aufgebaut(self):
        # Die fuenf Tages-Tabellen muessen bis auf Tagesname und Platzhalter
        # identisch sein (Rahmen, Breiten, Zeilenhoehen, Absatzformate).
        # Vorher waren sie Kopien, die unbemerkt auseinandergelaufen sind.
        tage = {"MONTAG": ("Montag", "MO"), "DIENSTAG": ("Dienstag", "DI"),
                "MITTWOCH": ("Mittwoch", "MI"), "DONNERSTAG": ("Donnerstag", "DO"),
                "FREITAG": ("Freitag", "FR")}
        xml = self.zip.read("word/document.xml").decode("utf-8")
        tabellen = re.findall(r"<w:tbl>.*?</w:tbl>", xml, re.S)

        def normalisiert(tag):
            name, kurz = tage[tag]
            treffer = [t for t in tabellen if "{{%s}}" % tag in t]
            self.assertEqual(len(treffer), 1, tag)
            t = treffer[0]
            # IDs, die Word pro Absatz/Kontrollkaestchen vergibt, sind egal
            t = re.sub(r' w14:(paraId|textId)="[^"]*"', "", t)
            t = re.sub(r' w:rsid\w*="[^"]*"', "", t)
            t = re.sub(r'<w:id w:val="-?\d+"/>', "", t)
            t = t.replace("<w:lastRenderedPageBreak/>", "")
            return (t.replace(tag, "TAG").replace(f">{name}<", ">Tag<")
                     .replace(f"H_{kurz}", "H_TAG"))

        vorlage = normalisiert("DIENSTAG")
        for tag in tage:
            with self.subTest(tag=tag):
                self.assertEqual(normalisiert(tag), vorlage)


if __name__ == "__main__":
    unittest.main()
