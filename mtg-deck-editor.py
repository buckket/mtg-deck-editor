#!/usr/bin/python
# -*- coding: utf-8 -*-

#       Copyright 2015 Nils Dagsson Moskopp // erlehmann

#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

from __future__ import with_statement

from gi.repository import Gtk
import os

class MtgDeckEditor:
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file("Interface.GtkBuilder")
        builder.connect_signals(self)

        self.window = builder.get_object("window")

    def main(self):
        self.window.show_all()
        Gtk.main()

    def on_window_destroy(self, widget, data=None):
        Gtk.main_quit()

if __name__ == '__main__':
    mde = MtgDeckEditor()
    mde.main()
