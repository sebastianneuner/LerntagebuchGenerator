"""
Zentrale Pfade, Standardwerte und Einstellungen.

Alle Pfade haengen am App-Ordner, nicht am Arbeitsverzeichnis. So findet die
App ihre Dateien, egal von wo aus sie gestartet wird, und bleibt portabel:
nichts wird ausserhalb dieses Ordners geschrieben.

Die Standardwerte stehen hier im Code. Eigene Anpassungen liegen in
settings.json im App-Ordner und ueberschreiben die Standards. Fehlt die Datei,
gelten die Standards.
"""

import copy
import json
import sys
from pathlib import Path


def app_dirs():
    """(App-Ordner, Ordner mit den mitgelieferten Dateien) bestimmen.

    Aus dem Quellcode gestartet ist beides der Projektordner (eine Ebene ueber
    dem Paket lerntagebuch/). Als PyInstaller-Programm (sys.frozen) ist der
    App-Ordner der Ordner der .exe: Dort liegen die Nutzerdaten. Die
    mitgelieferte Vorlage liegt dann im Bundle (sys._MEIPASS, bei PyInstaller
    im Ordner-Modus der Unterordner _internal).
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent, Path(sys._MEIPASS)
    project = Path(__file__).resolve().parent.parent
    return project, project


APP_DIR, BUNDLE_DIR = app_dirs()

TEMPLATE_PATH = BUNDLE_DIR / "resources" / "template.docx"
WEEK_PATH = APP_DIR / "week.json"
OUTPUT_DIR = APP_DIR / "output"
SETTINGS_PATH = APP_DIR / "settings.json"

# Gueltige Lernort-Kuerzel. Die Kuerzel selbst sind nicht konfigurierbar,
# an ihnen haengt feste Logik (Checkboxen im Template, Lernfeld, Pflichtinhalt).
CODE_LABELS = {
    "S": "Akademie/Standort",
    "B": "Betrieb",
    "M": "Mobil",
    "F": "Feiertag",
    "U": "Urlaub",
}

# Beschriftung der Lernort-Kaestchen im Template (Textanfang hinter dem
# Kaestchen). Der Generator ordnet die Kaestchen darueber zu, nicht ueber
# ihre Reihenfolge.
LERNORT_CHECKBOX_LABELS = {
    "S": "Akademie",
    "B": "Betrieb",
    "M": "mobil",
}

DEFAULT_PATTERN = "MSSSM"

# Name in der Kopfzeile ({{NAME}} = "Nachname, Vorname"). Bewusst neutral.
DEFAULT_LAST_NAME = "Nachname"
DEFAULT_FIRST_NAME = "Vorname"

DEFAULT_LF = ""

# Unterschrift: Das Bild wird als unterschrift.<ext> in den App-Ordner kopiert
# (gitignored). Im Template steht ein Bild-Platzhalter, erkennbar am
# Alternativtext {{UNTERSCHRIFT}}.
SIGNATURE_STEM = "unterschrift"
SIGNATURE_EXTENSIONS = (".png", ".jpg", ".jpeg")
SIGNATURE_PLACEHOLDER = "{{UNTERSCHRIFT}}"

# Stunden je Lernort-Kuerzel und Wochentag (Mo, Di, Mi, Do, Fr).
DEFAULT_HOURS = {
    "S": [10, 10, 10, 10, 7],
    "B": [8.5, 8.5, 8.5, 8.5, 6],
    "M": [10, 10, 10, 10, 7],
    "F": [0, 0, 0, 0, 0],
    "U": [0, 0, 0, 0, 0],
}
MAX_HOURS = 24


def default_settings():
    """Frische Kopie der Standardeinstellungen."""
    return {
        "last_name": DEFAULT_LAST_NAME,
        "first_name": DEFAULT_FIRST_NAME,
        "hours": copy.deepcopy(DEFAULT_HOURS),
        "default_pattern": DEFAULT_PATTERN,
        "default_lf": DEFAULT_LF,
        "output_dir": "",  # leer = Standard (output/ im App-Ordner)
        "signature": "",   # leer = keine Unterschrift, sonst Dateiname im App-Ordner
        "signature_name": False,  # True = Nachname als Unterschrift statt Bild
    }


# ------------------------------------------------------------------ Stunden
def parse_hours(value):
    """Wandelt eine Stundenangabe in eine Zahl um: '8,5', '8.5' oder 8.5 -> 8.5.

    Wirft ValueError bei leeren, nicht-numerischen oder unplausiblen Werten
    (erlaubt ist 0 bis MAX_HOURS).
    """
    if isinstance(value, bool):  # bool ist in Python ein int, hier aber falsch
        raise ValueError("keine Zahl")
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = str(value).strip().replace(",", ".")
        if not text:
            raise ValueError("leer")
        number = float(text)
    # Die Bedingung faengt auch NaN ab, weil jeder Vergleich mit NaN False ist.
    if not 0 <= number <= MAX_HOURS:
        raise ValueError(f"nicht zwischen 0 und {MAX_HOURS}")
    return number


def format_hours(value):
    """Zahl fuer das Dokument formatieren: 10.0 -> '10', 8.5 -> '8,5'."""
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:g}".replace(".", ",")


def is_valid_pattern(pattern):
    return len(pattern) == 5 and all(c in CODE_LABELS for c in pattern)


def full_name(settings):
    """Name fuer die Kopfzeile: "Nachname, Vorname"."""
    return ", ".join(p for p in (settings["last_name"], settings["first_name"]) if p)


# ---------------------------------------------------------- settings.json
def load_settings(path=None):
    """Liest settings.json und ergaenzt fehlende oder ungueltige Werte mit Standards.

    Gibt (settings, warnungen) zurueck. Wirft keine Fehler: Eine kaputte Datei
    soll die App nicht am Starten hindern, der Nutzer bekommt stattdessen die
    Warnungen angezeigt.
    """
    path = Path(path or SETTINGS_PATH)
    settings = default_settings()
    warnings = []

    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except FileNotFoundError:
        return settings, warnings
    except (OSError, ValueError) as e:  # ValueError umfasst JSONDecodeError
        warnings.append(f"{path.name} konnte nicht gelesen werden ({e}). "
                        "Es gelten die Standardwerte.")
        return settings, warnings

    if not isinstance(data, dict):
        warnings.append(f"{path.name} hat ein unerwartetes Format. "
                        "Es gelten die Standardwerte.")
        return settings, warnings

    # Aeltere settings.json haben nur "name" als "Nachname, Vorname".
    # Beim naechsten Speichern stehen dann die beiden neuen Felder drin.
    if "name" in data and "last_name" not in data and "first_name" not in data:
        name = data["name"]
        if isinstance(name, str) and name.strip():
            last, _, first = name.partition(",")
            data["last_name"], data["first_name"] = last.strip(), first.strip()

    for key, label, default in (("last_name", "Nachname", DEFAULT_LAST_NAME),
                                ("first_name", "Vorname", DEFAULT_FIRST_NAME)):
        if key in data:
            value = data[key]
            if isinstance(value, str) and value.strip():
                settings[key] = value.strip()
            else:
                warnings.append(f"{label} ist ungültig, es gilt „{default}“.")

    hours = data.get("hours", {})
    if not isinstance(hours, dict):
        warnings.append("Stunden sind ungültig, es gelten die Standardwerte.")
        hours = {}
    for code in DEFAULT_HOURS:
        if code not in hours:
            continue
        try:
            values = [parse_hours(v) for v in hours[code]]
            if len(values) != 5:
                raise ValueError("nicht genau 5 Werte")
            settings["hours"][code] = values
        except (TypeError, ValueError):
            warnings.append(f"Stunden für '{code}' sind ungültig, "
                            "es gelten die Standardwerte.")

    if "default_pattern" in data:
        pattern = data["default_pattern"]
        if isinstance(pattern, str) and is_valid_pattern(pattern.upper()):
            settings["default_pattern"] = pattern.upper()
        else:
            warnings.append("Standard-Lernort ist ungültig, "
                            f"es gilt {DEFAULT_PATTERN}.")

    if isinstance(data.get("default_lf"), str):
        settings["default_lf"] = data["default_lf"].strip()

    if isinstance(data.get("output_dir"), str):
        settings["output_dir"] = data["output_dir"].strip()

    if isinstance(data.get("signature"), str):
        settings["signature"] = data["signature"].strip()

    if isinstance(data.get("signature_name"), bool):
        settings["signature_name"] = data["signature_name"]

    return settings, warnings


def save_settings(settings, path=None):
    """Schreibt settings.json.

    Erst in eine Temp-Datei, dann umbenennen: Bricht das Schreiben ab, bleibt
    die alte Datei heil statt halb geschrieben.
    """
    path = Path(path or SETTINGS_PATH)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


# ------------------------------------------------------------- Speicherort
def resolve_output_dir(settings):
    """Ordner fuer die erzeugten Dokumente bestimmen.

    Gibt (ordner, fallback) zurueck. fallback ist True, wenn ein eigener Ordner
    eingestellt ist, der aber nicht existiert (z. B. auf einem anderen Rechner).
    Dann wird in den Standardordner gespeichert.

    Relative Pfade gelten relativ zum App-Ordner. So bleibt ein Ordner innerhalb
    der App auch nach dem Verschieben der App gueltig.
    """
    custom = settings.get("output_dir", "")
    if not custom:
        return OUTPUT_DIR, False
    path = Path(custom)
    if not path.is_absolute():
        path = APP_DIR / path
    if path.is_dir():
        return path, False
    return OUTPUT_DIR, True


def portable_path(path):
    """Ordner innerhalb des App-Ordners relativ speichern, alle anderen absolut."""
    path = Path(path).resolve()
    try:
        return path.relative_to(APP_DIR).as_posix()
    except ValueError:
        return str(path)


# ------------------------------------------------------------- Unterschrift
def signature_text(settings):
    """Nachname als Unterschrift, falls so eingestellt, sonst ""."""
    if not settings.get("signature_name"):
        return ""
    return settings["last_name"]


def resolve_signature(settings):
    """Pfad zum Unterschriftsbild bestimmen.

    Gibt (pfad, fehlt) zurueck: (None, False) wenn keine Unterschrift
    eingestellt ist, (None, True) wenn sie eingestellt ist, die Datei aber fehlt.
    Relative Angaben gelten relativ zum App-Ordner.
    """
    value = settings.get("signature", "")
    if not value:
        return None, False
    path = Path(value)
    if not path.is_absolute():
        path = APP_DIR / path
    if path.is_file():
        return path, False
    return None, True


def check_signature_image(path):
    """Prueft, ob die Datei als Unterschrift taugt. Gibt eine Fehlermeldung oder None zurueck."""
    path = Path(path)
    if path.suffix.lower() not in SIGNATURE_EXTENSIONS:
        return "Bitte ein PNG- oder JPG-Bild wählen."
    try:
        from docx.image.image import Image  # dieselbe Pruefung wie beim Einfuegen
        Image.from_file(str(path))
    except Exception:
        return f"„{path.name}“ ist kein lesbares Bild."
    return None


def store_signature(source, target_dir=None):
    """Kopiert das Unterschriftsbild als unterschrift.<ext> in den App-Ordner.

    Gibt den Dateinamen zurueck. So bleibt die App portabel, die Originaldatei
    wird danach nicht mehr gebraucht. Eine vorhandene Unterschrift (auch mit
    anderer Endung) wird ersetzt.
    """
    source = Path(source)
    target_dir = Path(target_dir or APP_DIR)
    data = source.read_bytes()  # vorher lesen: source kann die alte Datei selbst sein
    remove_signature(target_dir)
    target = target_dir / f"{SIGNATURE_STEM}{source.suffix.lower()}"
    target.write_bytes(data)
    return target.name


def remove_signature(target_dir=None):
    """Loescht die Kopie des Unterschriftsbilds im App-Ordner (falls vorhanden)."""
    target_dir = Path(target_dir or APP_DIR)
    for ext in SIGNATURE_EXTENSIONS:
        (target_dir / f"{SIGNATURE_STEM}{ext}").unlink(missing_ok=True)
