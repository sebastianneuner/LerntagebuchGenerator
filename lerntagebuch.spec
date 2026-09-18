# PyInstaller-Konfiguration fuer die ausfuehrbare App.
#
# Bauen (im Projektordner, mit dem venv-Python):
#     .venv\Scripts\python.exe -m PyInstaller lerntagebuch.spec   (Windows)
#     .venv/bin/python -m PyInstaller lerntagebuch.spec           (Linux)
#
# Ergebnis: dist/Lerntagebuch/ ist der fertige App-Ordner (Ordner-Modus, keine
# einzelne .exe). Nutzerdaten (settings.json, week.json, output/) landen neben
# der .exe, die Vorlage liegt im Unterordner _internal (siehe config.app_dirs).

a = Analysis(
    ["lerntagebuch/__main__.py"],
    pathex=["."],
    datas=[("resources/template.docx", "resources")],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Lerntagebuch",
    console=False,  # GUI-App: kein Konsolenfenster
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="Lerntagebuch",
    upx=False,
)
