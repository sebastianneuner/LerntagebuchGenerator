"""Kleine GUI-Helfer, die Tkinter nicht von Haus aus mitbringt."""

import sys
import tkinter as tk
from tkinter import font as tkfont


class ToolTip:
    """Zeigt nach kurzer Verzoegerung einen Hinweistext, solange die Maus ueber
    dem Widget steht. Verschwindet beim Verlassen oder Klicken."""

    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._after_id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self):
        self._after_id = None
        if self._tip or not self.widget.winfo_exists():
            return
        x = self.widget.winfo_rootx() + 16
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._tip = tip = tk.Toplevel(self.widget)
        tip.wm_overrideredirect(True)  # ohne Rahmen und Titelleiste
        tip.wm_geometry(f"+{x}+{y}")
        # Farben fest setzen: Unter dunklen Linux-Themes waere der Text sonst
        # evtl. hell auf hellem Grund.
        tk.Label(tip, text=self.text, justify="left",
                 background="#ffffe0", foreground="#000000",
                 relief="solid", borderwidth=1, padx=6, pady=3).pack()

    def _hide(self, _event=None):
        self._cancel()
        if self._tip:
            self._tip.destroy()
            self._tip = None


def fixed_font(size=11):
    """Schrift mit fester Zeichenbreite fuer das Lernort-Feld.

    Unter Windows Consolas (wie bisher). Andere Systeme haben Consolas meist
    nicht, dort die Festbreiten-Standardschrift von Tk.

    Der Rueckgabewert muss vom Aufrufer gehalten werden (z. B. als Attribut),
    sonst raeumt Python das Font-Objekt weg und Tk faellt auf die
    Standardschrift zurueck.
    """
    if sys.platform == "win32":
        return tkfont.Font(family="Consolas", size=size)
    font = tkfont.nametofont("TkFixedFont").copy()
    font.configure(size=size)
    return font
