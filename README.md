# Lerntagebuch-Generator

Erstellt dein wöchentliches Lerntagebuch als Word-Dokument (`.docx`). Du trägst
pro Woche nur Kalenderwoche, Lernort und die Tagesinhalte ein, den Rest
(Datum, Stunden, Kästchen, Name, Unterschrift) füllt die App aus.

Läuft unter **Windows** und **Linux**. Es muss nichts installiert werden.

---

## Herunterladen und starten

1. Auf der Seite **[Releases](../../releases/latest)** die passende Datei laden:
   - Windows: `Lerntagebuch-…-windows.zip`
   - Linux: `Lerntagebuch-…-linux.tar.gz`
2. Entpacken, an einen beliebigen Ort (z. B. *Dokumente* oder ein USB-Stick).
   - Windows: Rechtsklick auf die ZIP → **Alle extrahieren…**. Nicht direkt
     aus der ZIP heraus starten.
   - Linux: `tar -xzf Lerntagebuch-…-linux.tar.gz`
3. Starten:
   - Windows: im Ordner `Lerntagebuch` auf **`Lerntagebuch.exe`** doppelklicken.
   - Linux: `./Lerntagebuch/Lerntagebuch`

### Windows warnt beim ersten Start

Die App ist nicht digital signiert (das kostet Geld und lohnt sich für ein
kleines Projekt nicht). Windows reagiert darauf je nach Einstellung:

**„Der Computer wurde durch Windows geschützt“ (SmartScreen)**
Auf **Weitere Informationen** klicken, dann auf **Trotzdem ausführen**. Das ist
nur beim ersten Start nötig.

**„Intelligente App-Steuerung“ / „Smart App Control“ hat die App blockiert**
Diese Funktion lässt unsignierte Programme grundsätzlich nicht zu, eine
Ausnahme nur für diese App gibt es nicht. Die App läuft dann nur, wenn du die
intelligente App-Steuerung ausschaltest: *Windows-Sicherheit → App- &
Browsersteuerung → Intelligente App-Steuerung*.
Überlege dir das gut: Sie schützt vor Schadsoftware. Ab Windows 11 Version
25H2 kannst du sie später wieder einschalten, bei älteren Versionen geht das
nur mit einer Neuinstallation von Windows.

Auf Firmen- oder Schul-PCs können beide Wege gesperrt sein.

---

## Erster Start: Einstellungen

Über **Einstellungen…** einmalig eintragen:

- **Nachname** und **Vorname**: stehen oben im Dokument
- **Standard-Lernort**: dein übliches Wochenmuster, z. B. `MSSSM`
- **Stunden je Lernort**: falls sie bei dir anders sind
- **Speicherort**: wohin die Dokumente gespeichert werden
  (Standard: Ordner `output` in der App)
- **Unterschrift**: entweder ein Bild deiner Unterschrift (PNG oder JPG, am
  besten eng zugeschnitten) oder **Nachnamen als Unterschrift einsetzen**

Alle Felder haben Hinweise, wenn du mit der Maus darüber fährst.

## Jede Woche

1. **Jahr** und **KW** prüfen.
2. **Lernort** für Montag bis Freitag, genau 5 Zeichen:

   | Zeichen | Bedeutung |
   |---|---|
   | `S` | Akademie/Standort |
   | `B` | Betrieb |
   | `M` | Mobil |
   | `F` | Feiertag |
   | `U` | Urlaub |

   Beispiel: `SSBBF` = Montag und Dienstag Akademie, Mittwoch und Donnerstag
   Betrieb, Freitag Feiertag.
3. Optional das **Lernfeld**, z. B. `5` oder `5, 7`.
4. Die **Inhalte** für jeden Arbeitstag eintragen.
5. **Generieren**. Das Dokument heißt `Lerntagebuch_KW<KW>_<Jahr>.docx`.

Deine Eingaben bleiben beim nächsten Start erhalten.

---

## Deine Daten und Updates

Alles liegt im Ordner der App, nichts wird woanders gespeichert:

| Datei | Inhalt |
|---|---|
| `settings.json` | deine Einstellungen |
| `unterschrift.png` / `.jpg` | dein Unterschriftsbild (falls gewählt) |
| `week.json` | die zuletzt eingetragene Woche |
| `output/` | die erzeugten Dokumente (wenn nichts anderes eingestellt ist) |

**Neue Version installieren:** neue Version entpacken und die Dateien aus der
Tabelle aus dem alten Ordner in den neuen kopieren. Danach kann der alte
Ordner weg.

---

## Für Entwickler

Python 3.12, Tkinter, python-docx. Im Projektordner:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt        # Windows: .venv\Scripts\pip ...
.venv/bin/python -m lerntagebuch                  # App starten
.venv/bin/python -m unittest discover -s tests    # Tests
```

Unter Linux fehlt Tkinter oft im System-Python (Debian/Ubuntu:
`sudo apt install python3-tk`).

**App bauen:** `pip install -r requirements-dev.txt`, dann
`python -m PyInstaller lerntagebuch.spec`. Ergebnis: `dist/Lerntagebuch/`.

**Release:** Ein Tag wie `v1.0.0` pushen. GitHub Actions baut dann Windows- und
Linux-Version und hängt sie an ein Release (`.github/workflows/release.yml`).

---

## Lizenz

[MIT](LICENSE): Du darfst die App frei nutzen, verändern und weitergeben,
solange der Lizenzhinweis erhalten bleibt. Ohne Gewähr.
