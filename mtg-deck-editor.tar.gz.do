#!/bin/sh
FILES='Interface.GtkBuilder mtg-deck-editor.py README test.dek'
redo-ifchange $FILES
tar -cvzf - $FILES 2>/dev/null
