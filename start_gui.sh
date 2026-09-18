#!/bin/sh
# Startet das Lerntagebuch-Frontend mit dem Python der virtuellen Umgebung.
cd "$(dirname "$0")"
exec .venv/bin/python -m lerntagebuch
