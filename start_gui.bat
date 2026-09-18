@echo off
rem Startet das Lerntagebuch-Frontend mit dem Python der virtuellen Umgebung.
cd /d "%~dp0"
start "" ".venv\Scripts\pythonw.exe" -m lerntagebuch
