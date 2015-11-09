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

from gi.repository import Gio
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf

from requests import get
from html5lib import parse

import os
import re

class MtgDeckEditor:
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file("Interface.GtkBuilder")
        builder.connect_signals(self)

        self.window = builder.get_object("window")
        self.image_card = builder.get_object("image_card")

    def main(self):
        self.window.show_all()
        Gtk.main()

    def on_window_destroy(self, widget, data=None):
        Gtk.main_quit()

    def on_searchentry_activate(self, widget, data=None):
        query = widget.get_text()
        card = Card(query)
        self.image_card.set_from_pixbuf(card.pixbuf)
        print card

class Card:
    def __init__(self, query):
        image_url = \
            "http://gatherer.wizards.com/Handlers/Image.ashx?type=card&name=%s" % \
            query
        # rotate split cards
        if '//' in query:
            image_url= '%s&options=rotate90' % image_url
        print image_url
        image_raw = get(image_url).content
        input_stream = Gio.MemoryInputStream.new_from_data(image_raw, None)
        self.pixbuf = Pixbuf.new_from_stream(input_stream, None)

        # handle split cards
        query = re.sub("(.*) // (.*)", r"[\1]+[//]+[\2]", query)
        html_url = \
            "http://gatherer.wizards.com/Pages/Card/Details.aspx?name=%s" % \
            query
        html = get(html_url).text
        self.dom = parse(html, treebuilder='etree', namespaceHTMLElements=False)

    @property
    def name(self):
        xpath = ".//*[@id='ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_" + \
            "%sRow']/div" % 'name'
        return self.dom.findall(xpath)[1].text.strip()

    @property
    def type(self):
        xpath = ".//*[@id='ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_" + \
            "%sRow']/div" % 'type'
        return self.dom.findall(xpath)[1].text.strip()

    @property
    def cmc(self):
        xpath = ".//*[@id='ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_" + \
            "%sRow']/div" % 'cmc'
        return self.dom.findall(xpath)[1].text.strip()

    @property
    def text(self):
        xpath = ".//*[@id='ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_" + \
            "%sRow']/div/div" % 'text'
        return self.dom.findall(xpath)[0].text.strip()

    def __str__(self):
        return "%s | %s | %s | %s" % (self.name, self.type, self.cmc, self.text)

if __name__ == '__main__':
    mde = MtgDeckEditor()
    mde.main()
