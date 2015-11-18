#!/bin/sh
FILES='Interface.GtkBuilder mtg_deck_editor.py README LICENSE MANIFEST.in setup.py test.dek'
redo-ifchange $FILES
tar -cvzf - $FILES 2>/dev/null
