"""
Grafisches Frontend fuer den Lerntagebuch-Generator.

Erfasst die Wochendaten mit Eingabekontrolle und Pflichtfeldpruefung,
schreibt week.json und startet die Dokumenterstellung aus generator.py.

Starten (im Projektordner):
    .venv\\Scripts\\python.exe -m lerntagebuch   (Windows)
    .venv/bin/python -m lerntagebuch           (Linux/macOS)
"""

import io
import json
import os
import subprocess
import sys
import tkinter as tk
from contextlib import redirect_stdout
from datetime import date, timedelta
from tkinter import messagebox, ttk

from lerntagebuch import config, generator
from lerntagebuch.gui.setup import SettingsDialog
from lerntagebuch.gui.widgets import fixed_font

DAYS = [
    ("montag", "Montag"),
    ("dienstag", "Dienstag"),
    ("mittwoch", "Mittwoch"),
    ("donnerstag", "Donnerstag"),
    ("freitag", "Freitag"),
]
VALID_CODES = "".join(config.CODE_LABELS)  # gueltige Lernort-Zeichen
WORKING_CODES = ("S", "B", "M")  # Tage mit Pflichtinhalt


def open_folder(path):
    """Oeffnet einen Ordner im Dateimanager des jeweiligen Systems.

    os.startfile gibt es nur unter Windows. Der Aufruf steht deshalb im
    if-Zweig: dort wird er auf anderen Systemen nie ausgefuehrt, und das
    dort fehlende Attribut faellt nicht auf.
    """
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])


class LerntagebuchGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lerntagebuch Generator")
        self.resizable(False, False)

        self.settings, settings_warnings = config.load_settings()
        self._fixed_font = fixed_font()

        self.jahr_var = tk.StringVar(value=str(date.today().year))
        self.kw_var = tk.StringVar(value=str(date.today().isocalendar()[1]))
        self.lernort_var = tk.StringVar(value=self.settings["default_pattern"])
        self.lf_var = tk.StringVar(value=self.settings["default_lf"])
        self.status_var = tk.StringVar(value="Bereit.")

        # key -> dict(date_lbl, hours_lbl, place_lbl, text, name_lbl, label)
        self.day_widgets = {}

        self._build_widgets()
        self._load_existing()

        # Live aktualisieren, sobald sich Jahr, KW oder Lernort aendern.
        self.jahr_var.trace_add("write", lambda *_: self._refresh())
        self.kw_var.trace_add("write", lambda *_: self._refresh())
        self.lernort_var.trace_add("write", self._on_lernort_change)
        self._refresh()

        if settings_warnings:
            # Erst anzeigen, wenn das Hauptfenster steht.
            self.after(200, lambda: messagebox.showwarning(
                "Einstellungen", "\n\n".join(settings_warnings), parent=self))

    # ------------------------------------------------------------------ UI
    def _build_widgets(self):
        pad = {"padx": 6, "pady": 4}
        root = ttk.Frame(self, padding=12)
        root.grid(row=0, column=0)

        # --- Kopfzeile: Jahr / KW / Lernort / Lernfeld ---
        head = ttk.Frame(root)
        head.grid(row=0, column=0, sticky="w")

        ttk.Label(head, text="Jahr *").grid(row=0, column=0, **pad)
        ttk.Entry(head, textvariable=self.jahr_var, width=8).grid(row=0, column=1, **pad)

        ttk.Label(head, text="KW *").grid(row=0, column=2, **pad)
        ttk.Entry(head, textvariable=self.kw_var, width=6).grid(row=0, column=3, **pad)

        ttk.Label(head, text="Lernort *").grid(row=0, column=4, **pad)
        ttk.Entry(head, textvariable=self.lernort_var, width=8,
                  font=self._fixed_font).grid(row=0, column=5, **pad)

        ttk.Label(head, text="Lernfeld").grid(row=0, column=6, **pad)
        ttk.Entry(head, textvariable=self.lf_var, width=10).grid(row=0, column=7, **pad)
        ttk.Label(head, text="optional – z. B.  5   oder  5, 7, 9",
                  foreground="#555").grid(row=1, column=6, columnspan=2,
                                          padx=6, sticky="w")

        ttk.Separator(root, orient="horizontal").grid(
            row=1, column=0, sticky="ew", pady=(8, 4))

        # --- Tagesraster ---
        grid = ttk.Frame(root)
        grid.grid(row=2, column=0, sticky="w")

        for col, header in enumerate(["Tag", "Datum", "Std.", "Inhalt", "Lernort"]):
            ttk.Label(grid, text=header, font=("", 9, "bold")).grid(
                row=0, column=col, padx=6, pady=(0, 4), sticky="w")

        for i, (key, label) in enumerate(DAYS):
            r = i + 1

            name_lbl = ttk.Label(grid, text=label)
            name_lbl.grid(row=r, column=0, padx=6, pady=4, sticky="nw")

            date_lbl = ttk.Label(grid, text="--", foreground="#555")
            date_lbl.grid(row=r, column=1, padx=6, pady=4, sticky="nw")

            hours_lbl = ttk.Label(grid, text="-", width=4)
            hours_lbl.grid(row=r, column=2, padx=6, pady=4, sticky="nw")

            text = tk.Text(grid, width=54, height=3, wrap="word")
            text.grid(row=r, column=3, padx=6, pady=4)

            # Breite fuer den laengsten Namen ("Akademie/Standort"), damit das
            # Fenster beim Tippen nicht springt
            place_lbl = ttk.Label(grid, text="-", foreground="#555",
                                  width=max(len(l) for l in config.CODE_LABELS.values()))
            place_lbl.grid(row=r, column=4, padx=6, pady=4, sticky="nw")

            self.day_widgets[key] = {
                "date_lbl": date_lbl,
                "hours_lbl": hours_lbl,
                "place_lbl": place_lbl,
                "text": text,
                "name_lbl": name_lbl,
                "label": label,
            }

        # --- Legende ---
        legend = ("Lernort: 5 Zeichen, gültig sind S/B/M/F/U  "
                  "(S = Akademie/Standort, B = Betrieb, M = Mobil, "
                  "F = Feiertag, U = Urlaub).        "
                  "* = Pflichtfeld (Inhalt an Arbeitstagen S/B/M)")
        ttk.Label(root, text=legend, foreground="#555").grid(
            row=3, column=0, sticky="w", pady=(8, 0))

        # --- Status ---
        ttk.Label(root, textvariable=self.status_var, foreground="#006400").grid(
            row=4, column=0, sticky="w", pady=(8, 0))

        # --- Buttons ---
        btns = ttk.Frame(root)
        btns.grid(row=5, column=0, sticky="e", pady=(10, 0))
        ttk.Button(btns, text="Einstellungen…", command=self.open_settings).grid(
            row=0, column=0, padx=(6, 24))
        ttk.Button(btns, text="Leeren", command=self.clear_form).grid(row=0, column=1, padx=6)
        ttk.Button(btns, text="Generieren", command=self.generate).grid(row=0, column=2, padx=6)

    # -------------------------------------------------------------- Helpers
    def _on_lernort_change(self, *_):
        """Eingabe normalisieren: Grossbuchstaben, nur S/B/M/F/U, max. 5 Zeichen."""
        raw = self.lernort_var.get()
        cleaned = "".join(c for c in raw.upper() if c in VALID_CODES)[:5]
        if cleaned != raw:
            self.lernort_var.set(cleaned)  # loest diesen Trace erneut aus -> dann no-op
            return
        self._refresh()

    def _refresh(self):
        """Datumsangaben, Stunden, Lernort und Pflichtfeld-Sternchen aktualisieren."""
        try:
            monday = date.fromisocalendar(
                int(self.jahr_var.get()), int(self.kw_var.get()), 1)
        except (ValueError, TypeError):
            monday = None

        pattern = self.lernort_var.get()
        hours = generator.calculate_hours(pattern, self.settings["hours"])  # Laenge == len(pattern)

        for i, (key, label) in enumerate(DAYS):
            w = self.day_widgets[key]
            if monday:
                w["date_lbl"].config(text=(monday + timedelta(days=i)).strftime("%d.%m.%Y"))
            else:
                w["date_lbl"].config(text="--")

            if i < len(pattern):
                w["hours_lbl"].config(text=hours[i])
                w["place_lbl"].config(text=config.CODE_LABELS[pattern[i]])
                star = " *" if pattern[i] in WORKING_CODES else ""
            else:
                w["hours_lbl"].config(text="-")
                w["place_lbl"].config(text="-")
                star = ""
            w["name_lbl"].config(text=label + star)

    def _load_existing(self):
        """Vorhandene week.json beim Start einlesen, falls vorhanden."""
        try:
            with open(config.WEEK_PATH, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return

        if data.get("jahr"):
            self.jahr_var.set(str(data["jahr"]))
        if data.get("kw"):
            self.kw_var.set(str(data["kw"]))
        self.lf_var.set(str(data.get("lf", "")))
        self.lernort_var.set(generator.get_lernort_pattern(data))

        for key, _ in DAYS:
            content = str(data.get(key, ""))
            if content:
                self.day_widgets[key]["text"].insert("1.0", content)

    # ----------------------------------------------------------- Validation
    def _validate(self):
        errors = []

        jahr = self.jahr_var.get().strip()
        year_val = None
        if not jahr:
            errors.append("Jahr ist ein Pflichtfeld.")
        elif not jahr.isdigit() or not (2000 <= int(jahr) <= 2100):
            errors.append("Jahr muss eine Zahl zwischen 2000 und 2100 sein.")
        else:
            year_val = int(jahr)

        kw = self.kw_var.get().strip()
        kw_val = None
        if not kw:
            errors.append("Kalenderwoche ist ein Pflichtfeld.")
        elif not kw.isdigit() or not (1 <= int(kw) <= 53):
            errors.append("Kalenderwoche muss eine Zahl zwischen 1 und 53 sein.")
        else:
            kw_val = int(kw)

        if year_val and kw_val:
            try:
                date.fromisocalendar(year_val, kw_val, 1)
            except ValueError:
                errors.append(f"KW {kw_val} existiert im Jahr {year_val} nicht.")

        pattern = self.lernort_var.get()
        if len(pattern) != 5:
            errors.append(
                f"Lernort muss genau 5 Zeichen lang sein (aktuell {len(pattern)}).")
        else:
            for i, (key, label) in enumerate(DAYS):
                content = self.day_widgets[key]["text"].get("1.0", "end").strip()
                if pattern[i] in WORKING_CODES and not content:
                    errors.append(f"{label}: Inhalt fehlt (Arbeitstag '{pattern[i]}').")

        return errors

    # --------------------------------------------------------------- Actions
    def generate(self):
        errors = self._validate()
        if errors:
            messagebox.showerror(
                "Eingaben unvollständig",
                "Bitte korrigieren:\n\n• " + "\n• ".join(errors))
            self.status_var.set("Eingaben unvollständig.")
            return

        data = {
            "jahr": self.jahr_var.get().strip(),
            "kw": self.kw_var.get().strip(),
            "lernort": self.lernort_var.get(),
            "lf": self.lf_var.get().strip(),
        }
        for key, _ in DAYS:
            data[key] = self.day_widgets[key]["text"].get("1.0", "end").strip()

        out_dir, fallback = config.resolve_output_dir(self.settings)
        existing = generator.output_path(out_dir, data["kw"], data["jahr"])
        if existing.exists() and not messagebox.askyesno(
                "Woche schon vorhanden",
                f"KW {int(data['kw'])}/{int(data['jahr'])} gibt es schon:\n"
                f"{existing.resolve()}\n\nÜberschreiben?",
                icon="warning", default="no"):
            self.status_var.set("Abgebrochen, vorhandenes Dokument bleibt unverändert.")
            return

        try:
            with open(config.WEEK_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            messagebox.showerror("Fehler", f"week.json konnte nicht gespeichert werden:\n{e}")
            return

        _, signature_missing = config.resolve_signature(self.settings)
        signature_missing = signature_missing and not config.signature_text(self.settings)

        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                out_path = generator.generate_document(
                    output_dir=out_dir, settings=self.settings)
        except Exception as e:
            messagebox.showerror("Fehler bei der Generierung", f"{e}\n\n{buf.getvalue()}")
            self.status_var.set("Fehler bei der Generierung.")
            return

        if not out_path:
            messagebox.showerror(
                "Fehler bei der Generierung",
                buf.getvalue().strip() or "Unbekannter Fehler.")
            self.status_var.set("Fehler bei der Generierung.")
            return

        abs_path = os.path.abspath(out_path)
        self.status_var.set(f"Erstellt: {abs_path}")
        hint = ""
        if fallback:
            hint = (f"Hinweis: Der eingestellte Speicherort\n{self.settings['output_dir']}\n"
                    "existiert nicht. Gespeichert wurde im Standardordner.\n\n")
        if signature_missing:
            hint += (f"Hinweis: Das Unterschriftsbild {self.settings['signature']} "
                     "fehlt im App-Ordner. Das Unterschriftsfeld ist leer geblieben.\n\n")
        if messagebox.askyesno("Fertig", f"{hint}Dokument erstellt:\n{abs_path}\n\nOrdner öffnen?"):
            open_folder(os.path.dirname(abs_path))

    def clear_form(self):
        if not messagebox.askyesno("Leeren", "Alle Eingaben zurücksetzen?"):
            return
        self.jahr_var.set(str(date.today().year))
        self.kw_var.set(str(date.today().isocalendar()[1]))
        self.lernort_var.set(self.settings["default_pattern"])
        self.lf_var.set(self.settings["default_lf"])
        for key, _ in DAYS:
            self.day_widgets[key]["text"].delete("1.0", "end")
        self.status_var.set("Bereit.")
        self._refresh()

    def open_settings(self):
        SettingsDialog(self, self.settings, on_save=self._apply_settings)

    def _apply_settings(self, settings):
        """Wird vom Einstellungsfenster nach dem Speichern aufgerufen."""
        self.settings = settings
        self.status_var.set("Einstellungen gespeichert.")
        self._refresh()  # Stundenvorschau mit den neuen Werten


def main():
    LerntagebuchGUI().mainloop()


if __name__ == "__main__":
    main()
