"""
Einstellungsfenster.

Modal: Solange es offen ist, ist das Hauptfenster gesperrt. Uebernommen wird
erst mit "Speichern". "Alles zurücksetzen" fuellt nur die Felder mit den
Standardwerten, gespeichert wird auch dann erst mit "Speichern".
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from lerntagebuch import config
from lerntagebuch.gui.widgets import ToolTip, fixed_font

WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr"]

TIP_NAME = ("Erscheint in der Kopfzeile des Dokuments als\n"
            "„Nachname, Vorname“, z. B. Mustermann, Max.\n"
            "Der Nachname kann auch als Unterschrift dienen (siehe unten).")
TIP_PATTERN = ("Lernort-Muster für Montag bis Freitag, genau 5 Zeichen.\n"
               "S = Akademie/Standort, B = Betrieb, M = Mobil,\n"
               "F = Feiertag, U = Urlaub\n"
               "Wird beim ersten Start und bei „Leeren“ eingesetzt.\n"
               "Beispiel: MSSSM")
TIP_LF = ("Optional. Wird beim ersten Start und bei „Leeren“ eingesetzt.\n"
          "Beispiel: 5   oder   5, 7, 9")
TIP_HOURS = ("Stunden an diesem Tag, wenn dort dieser Lernort eingetragen ist.\n"
             f"Komma oder Punkt, z. B. 8,5 oder 8.5. Erlaubt: 0 bis {config.MAX_HOURS}.")
TIP_OUTPUT = ("Ordner für die erzeugten Dokumente.\n"
              "Standard: output/ im App-Ordner.\n"
              "Existiert der gewählte Ordner nicht (z. B. auf einem anderen\n"
              "Rechner), wird automatisch in den Standardordner gespeichert.")
TIP_SIGNATURE = ("Bild mit deiner Unterschrift (PNG oder JPG).\n"
                 "Am besten nur die Unterschrift ohne Rand, ideal als PNG mit\n"
                 "transparentem Hintergrund (z. B. mit dem Snipping Tool ausschneiden).\n"
                 "Wird in das Feld „Datum, Unterschrift Teilnehmer/in“ eingepasst,\n"
                 "das Seitenverhältnis bleibt erhalten.\n"
                 "Das Bild wird beim Speichern in den App-Ordner kopiert.")
TIP_SIGNATURE_NAME = ("Statt eines Bildes steht dein Nachname im Feld\n"
                      "„Datum, Unterschrift Teilnehmer/in“ hinter dem Datum.\n"
                      "Ein gewähltes Bild wird dann nicht verwendet.")
TIP_RESET = ("Setzt alle Felder auf die Standardwerte.\n"
             "Übernommen wird erst mit „Speichern“.")

STANDARD_OUTPUT_TEXT = "Standard (output/ im App-Ordner)"
NO_SIGNATURE_TEXT = "Keine (Feld bleibt leer)"


class SettingsDialog(tk.Toplevel):

    def __init__(self, master, settings, on_save):
        super().__init__(master)
        self.title("Einstellungen")
        self.resizable(False, False)
        self.transient(master)  # gehoert zum Hauptfenster, bleibt davor
        self._on_save = on_save

        self.last_name_var = tk.StringVar()
        self.first_name_var = tk.StringVar()
        self.pattern_var = tk.StringVar()
        self.lf_var = tk.StringVar()
        self.output_display_var = tk.StringVar()
        self._output_dir = ""  # "" = Standard
        self.signature_display_var = tk.StringVar()
        self._signature_value = ""    # gespeicherter Wert ("" = keine)
        self._signature_source = None  # neu gewaehlte Datei, kopiert wird beim Speichern
        self.signature_name_var = tk.BooleanVar()
        self.hour_vars = {code: [tk.StringVar() for _ in WEEKDAYS]
                          for code in config.CODE_LABELS}
        self._fixed_font = fixed_font()

        self._build()
        self._fill(settings)
        self.pattern_var.trace_add("write", self._on_pattern_change)

        self.protocol("WM_DELETE_WINDOW", self.destroy)  # X = Abbrechen
        self.bind("<Escape>", lambda _e: self.destroy())
        self.geometry(f"+{master.winfo_rootx() + 40}+{master.winfo_rooty() + 40}")

        # Modal machen. Unter Linux muss das Fenster sichtbar sein, bevor
        # grab_set() greift, sonst gibt es "grab failed: window not viewable".
        self.wait_visibility()
        self.grab_set()
        self.focus_set()

    # ------------------------------------------------------------------ UI
    def _build(self):
        pad = {"padx": 6, "pady": 4}
        root = ttk.Frame(self, padding=12)
        root.grid(row=0, column=0)

        # --- Allgemein ---
        general = ttk.LabelFrame(root, text="Allgemein", padding=8)
        general.grid(row=0, column=0, sticky="ew")

        rows = [
            ("Nachname *", self.last_name_var, 32, None, TIP_NAME),
            ("Vorname *", self.first_name_var, 32, None, TIP_NAME),
            ("Standard-Lernort *", self.pattern_var, 8, self._fixed_font, TIP_PATTERN),
            ("Standard-Lernfeld", self.lf_var, 12, None, TIP_LF),
        ]
        for r, (label, var, width, font, tip) in enumerate(rows):
            lbl = ttk.Label(general, text=label)
            lbl.grid(row=r, column=0, sticky="w", **pad)
            entry = ttk.Entry(general, textvariable=var, width=width)
            if font:
                entry.configure(font=font)
            entry.grid(row=r, column=1, sticky="w", **pad)
            ToolTip(lbl, tip)
            ToolTip(entry, tip)

        # --- Stunden je Lernort ---
        hours = ttk.LabelFrame(root, text="Stunden je Lernort", padding=8)
        hours.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        for c, day in enumerate(WEEKDAYS):
            ttk.Label(hours, text=day, font=("", 9, "bold")).grid(
                row=0, column=c + 1, padx=4, pady=(0, 4))

        for r, (code, label) in enumerate(config.CODE_LABELS.items(), start=1):
            ttk.Label(hours, text=f"{code} – {label}").grid(
                row=r, column=0, sticky="w", padx=(0, 10), pady=2)
            for c in range(len(WEEKDAYS)):
                entry = ttk.Entry(hours, textvariable=self.hour_vars[code][c],
                                  width=5, justify="center")
                entry.grid(row=r, column=c + 1, padx=4, pady=2)
                ToolTip(entry, TIP_HOURS)

        ttk.Label(hours, text="Komma oder Punkt, z. B. 8,5",
                  foreground="#555").grid(row=len(config.CODE_LABELS) + 1,
                                          column=0, columnspan=6, sticky="w",
                                          pady=(6, 0))

        # --- Speicherort ---
        output = ttk.LabelFrame(root, text="Speicherort", padding=8)
        output.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        out_entry = ttk.Entry(output, textvariable=self.output_display_var,
                              width=44, state="readonly")
        out_entry.grid(row=0, column=0, sticky="w", **pad)
        browse = ttk.Button(output, text="Durchsuchen…", command=self._browse)
        browse.grid(row=0, column=1, **pad)
        standard = ttk.Button(output, text="Standard",
                              command=lambda: self._set_output_dir(""))
        standard.grid(row=0, column=2, **pad)
        for w in (out_entry, browse):
            ToolTip(w, TIP_OUTPUT)
        ToolTip(standard, "Zurück zum Standardordner output/ im App-Ordner.")

        # --- Unterschrift ---
        signature = ttk.LabelFrame(root, text="Unterschrift", padding=8)
        signature.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        sig_entry = ttk.Entry(signature, textvariable=self.signature_display_var,
                              width=44, state="readonly")
        sig_entry.grid(row=0, column=0, sticky="w", **pad)
        sig_choose = ttk.Button(signature, text="Bild wählen…",
                                command=self._choose_signature)
        sig_choose.grid(row=0, column=1, **pad)
        sig_remove = ttk.Button(signature, text="Entfernen",
                                command=self._remove_signature)
        sig_remove.grid(row=0, column=2, **pad)
        for w in (sig_entry, sig_choose):
            ToolTip(w, TIP_SIGNATURE)
        ToolTip(sig_remove, "Keine Unterschrift einfügen, das Feld bleibt leer.\n"
                            "Wirksam erst mit „Speichern“.")
        self._signature_image_widgets = (sig_entry, sig_choose, sig_remove)

        sig_name = ttk.Checkbutton(signature, text="Nachnamen als Unterschrift einsetzen (statt Bild)",
                                   variable=self.signature_name_var,
                                   command=self._on_signature_name_change)
        sig_name.grid(row=1, column=0, columnspan=3, sticky="w", **pad)
        ToolTip(sig_name, TIP_SIGNATURE_NAME)

        # --- Buttons ---
        btns = ttk.Frame(root)
        btns.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        btns.columnconfigure(0, weight=1)
        reset = ttk.Button(btns, text="Alles zurücksetzen", command=self._reset)
        reset.grid(row=0, column=0, sticky="w")
        ToolTip(reset, TIP_RESET)
        ttk.Button(btns, text="Abbrechen", command=self.destroy).grid(
            row=0, column=1, padx=6)
        ttk.Button(btns, text="Speichern", command=self._save).grid(
            row=0, column=2)

        ttk.Label(root, text="* = Pflichtfeld   ·   Maus über ein Feld halten "
                             "zeigt einen Hinweis", foreground="#555").grid(
            row=5, column=0, sticky="w", pady=(8, 0))

    # --------------------------------------------------------------- Werte
    def _fill(self, settings):
        self.last_name_var.set(settings["last_name"])
        self.first_name_var.set(settings["first_name"])
        self.pattern_var.set(settings["default_pattern"])
        self.lf_var.set(settings["default_lf"])
        for code, values in settings["hours"].items():
            for i, value in enumerate(values):
                self.hour_vars[code][i].set(config.format_hours(value))
        self._set_output_dir(settings["output_dir"])
        self._signature_value = settings["signature"]
        self._signature_source = None
        self._show_signature()
        self.signature_name_var.set(settings["signature_name"])
        self._on_signature_name_change()

    def _set_output_dir(self, value):
        self._output_dir = value
        self.output_display_var.set(value or STANDARD_OUTPUT_TEXT)

    def _browse(self):
        start, _ = config.resolve_output_dir({"output_dir": self._output_dir})
        chosen = filedialog.askdirectory(parent=self, initialdir=start,
                                         title="Speicherort wählen")
        if chosen:  # leer = Dialog abgebrochen
            self._set_output_dir(config.portable_path(chosen))

    def _show_signature(self):
        if self._signature_source:
            text = f"Neu: {self._signature_source.name}"
        elif self._signature_value:
            _, missing = config.resolve_signature({"signature": self._signature_value})
            text = self._signature_value + ("  (Datei fehlt)" if missing else "")
        else:
            text = NO_SIGNATURE_TEXT
        self.signature_display_var.set(text)

    def _choose_signature(self):
        chosen = filedialog.askopenfilename(
            parent=self, title="Unterschrift wählen",
            filetypes=[("Bilder", "*.png *.jpg *.jpeg"), ("Alle Dateien", "*.*")])
        if not chosen:  # Dialog abgebrochen
            return
        error = config.check_signature_image(chosen)
        if error:
            messagebox.showerror("Unterschrift", error, parent=self)
            return
        self._signature_source = Path(chosen)
        self._show_signature()

    def _remove_signature(self):
        self._signature_value = ""
        self._signature_source = None
        self._show_signature()

    def _on_signature_name_change(self):
        """Mit Name als Unterschrift wird kein Bild verwendet: Bildauswahl sperren."""
        name_only = self.signature_name_var.get()
        for w in self._signature_image_widgets:
            if name_only:
                w.configure(state="disabled")
            else:  # das Anzeigefeld ist aktiv nur lesbar
                w.configure(state="readonly" if isinstance(w, ttk.Entry) else "normal")

    def _on_pattern_change(self, *_):
        """Wie im Hauptfenster: Grossbuchstaben, nur gueltige Kuerzel, max. 5."""
        raw = self.pattern_var.get()
        cleaned = "".join(c for c in raw.upper() if c in config.CODE_LABELS)[:5]
        if cleaned != raw:
            self.pattern_var.set(cleaned)

    def _reset(self):
        self._fill(config.default_settings())

    # ------------------------------------------------------------ Speichern
    def _collect(self):
        """Felder pruefen. Gibt (settings, fehler) zurueck."""
        errors = []

        last_name = self.last_name_var.get().strip()
        first_name = self.first_name_var.get().strip()
        if not last_name:
            errors.append("Nachname ist ein Pflichtfeld.")
        if not first_name:
            errors.append("Vorname ist ein Pflichtfeld.")

        pattern = self.pattern_var.get()
        if not config.is_valid_pattern(pattern):
            errors.append("Standard-Lernort muss genau 5 Zeichen aus "
                          "S/B/M/F/U haben.")

        hours = {}
        for code, vars_ in self.hour_vars.items():
            hours[code] = []
            for day, var in zip(WEEKDAYS, vars_):
                try:
                    hours[code].append(config.parse_hours(var.get()))
                except ValueError:
                    errors.append(f"Stunden {code} / {day}: „{var.get()}“ ist keine "
                                  f"gültige Zahl zwischen 0 und {config.MAX_HOURS}.")

        settings = {
            "last_name": last_name,
            "first_name": first_name,
            "hours": hours,
            "default_pattern": pattern,
            "default_lf": self.lf_var.get().strip(),
            "output_dir": self._output_dir,
            "signature": self._signature_value,
            "signature_name": self.signature_name_var.get(),
        }
        return settings, errors

    def _save(self):
        settings, errors = self._collect()
        if errors:
            messagebox.showerror("Eingaben prüfen",
                                 "Bitte korrigieren:\n\n• " + "\n• ".join(errors),
                                 parent=self)
            return
        try:
            # Unterschrift erst jetzt kopieren bzw. loeschen, damit "Abbrechen"
            # wirklich nichts veraendert.
            if self._signature_source:
                settings["signature"] = config.store_signature(self._signature_source)
            elif not settings["signature"]:
                config.remove_signature()
            config.save_settings(settings)
        except OSError as e:
            messagebox.showerror("Fehler",
                                 f"Einstellungen konnten nicht gespeichert werden:\n{e}",
                                 parent=self)
            return
        self._on_save(settings)
        self.destroy()
