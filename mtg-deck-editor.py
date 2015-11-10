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

from __future__ import print_function, with_statement

from gi.repository import Gio
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf

from functools32 import lru_cache
from random import shuffle
from requests import get
from html5lib import parse

import os
import re

from requests_cache import install_cache
install_cache('mtg-deck-editor-cache')

card_cache = {}

def get_card(query):
    try:
        return card_cache[query]
    except KeyError:
        card = Card(query)
        card_cache[query] = card
        return card

class MtgDeckEditor:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("Interface.GtkBuilder")
        self.builder.connect_signals(self)

        self.window_main = self.builder.get_object("window_main")
        self.window_hand = self.builder.get_object("window_hand")
        self.filechooserdialog_open = self.builder.get_object("filechooserdialog_open")
        self.image_card = self.builder.get_object("image_card")
        self.searchentry = self.builder.get_object("searchentry")
        self.liststore_deck = self.builder.get_object("liststore_deck")
        self.adjustment_card_amount = self.builder.get_object("adjustment_card_amount")

    def main(self):
        self.window_main.show_all()
        Gtk.main()

    def clear(self):
        for row in self.liststore_deck:
            self.liststore_deck.remove(row.iter)

    def on_window_main_destroy(self, widget, data=None):
        Gtk.main_quit()

    def on_searchentry_activate(self, widget, data=None):
        query = widget.get_text()
        card = get_card(query)
        self.image_card.set_from_pixbuf(card.pixbuf)

    def on_button_new_clicked(self, widget, data=None):
        self.clear()

    def on_button_card_add_clicked(self, widget, data=None):
        query = self.searchentry.get_text()
        card = get_card(query)
        new_amount = self.adjustment_card_amount.get_value()
        for row in self.liststore_deck:
            amount = row[0]
            name = row[1]
            if name == card.name:
                self.liststore_deck.remove(row.iter)
                new_amount = amount + self.adjustment_card_amount.get_value()
                break
        self.liststore_deck.append([new_amount, card.name])

    def on_button_card_remove_clicked(self, widget, data=None):
        query = self.searchentry.get_text()
        card = get_card(query)
        new_amount = 0
        for row in self.liststore_deck:
            amount = row[0]
            name = row[1]
            if name == card.name:
                self.liststore_deck.remove(row.iter)
                new_amount = amount - self.adjustment_card_amount.get_value()
                break
        if new_amount > 0:
            self.liststore_deck.append([new_amount, card.name])

    def on_button_open_clicked(self, widget, data=None):
        self.filechooserdialog_open.show()

    def on_button_open_cancel_clicked(self, widget, data=None):
        self.filechooserdialog_open.hide()

    def on_button_open_file_clicked(self, widget, data=None):
        self.filechooserdialog_open.hide()
        filename = self.filechooserdialog_open.get_filename()
        self.clear()
        with open(filename) as deckfile:
            data = deckfile.read()
            for line in data.split('\n'):
                tokens = line.split(' ')
                try:
                    amount = int(tokens[0])
                except ValueError:
                    continue
                name = ' '.join(tokens[1:])
                if name != '':
                    card = get_card(name)
                    self.liststore_deck.append([amount, card.name])

    def draw_hand(self, size):
        library = Library(self.liststore_deck)
        library.shuffle()
        for i in range(7):
            image_hand = self.builder.get_object("image_hand%s" % i)
            card = library.draw()
            if i < size:
                image_hand.set_from_pixbuf(card.pixbuf)
                image_hand.show()
            else:
                image_hand.hide()

    def on_button_hand_clicked(self, widget, data=None):
        self.draw_hand(7)
        self.window_hand.show_all()

    def on_button_hand_close_clicked(self, widget, data=None):
        self.window_hand.hide()

    def on_button_hand_mulligan_6_clicked(self, widget, data=None):
        widget.hide()
        self.draw_hand(6)
        self.builder.get_object("button_hand_mulligan_5").show()

    def on_button_hand_mulligan_5_clicked(self, widget, data=None):
        widget.hide()
        self.draw_hand(5)
        self.builder.get_object("button_hand_mulligan_4").show()

    def on_button_hand_mulligan_4_clicked(self, widget, data=None):
        widget.hide()
        self.draw_hand(4)
        self.builder.get_object("button_hand_mulligan_3").show()

    def on_button_hand_mulligan_3_clicked(self, widget, data=None):
        widget.hide()
        self.draw_hand(3)
        self.builder.get_object("button_hand_mulligan_2").show()

    def on_button_hand_mulligan_2_clicked(self, widget, data=None):
        widget.hide()
        self.draw_hand(2)
        self.builder.get_object("button_hand_mulligan_1").show()

    def on_button_hand_mulligan_1_clicked(self, widget, data=None):
        widget.hide()
        self.draw_hand(1)

    def on_treeview_selection_changed(self, widget, data=None):
        tree, i = widget.get_selected()
        self.searchentry.set_text(tree[i][1])
        self.searchentry.activate()

    def on_window_hand_delete_event(self, widget, data=None):
        self.window_hand.hide()
        return True

class Library:
    def __init__(self, liststore):
        self.cards = []
        for row in liststore:
            amount = row[0]
            name = row[1]
            self.cards.extend(amount*[name])

    def shuffle(self):
        shuffle(self.cards)

    def draw(self):
        return get_card(self.cards.pop())

lru_cache(maxsize=None)
class Card:
    def __init__(self, query):
        image_url = \
            "http://gatherer.wizards.com/Handlers/Image.ashx?type=card&name=%s" % \
            query
        # rotate split cards
        if '//' in query:
            image_url= '%s&options=rotate90' % image_url
        image_raw = get(image_url).content
        input_stream = Gio.MemoryInputStream.new_from_data(image_raw, None)
        self.pixbuf = Pixbuf.new_from_stream(input_stream, None)

        # handle split cards
        html_url = \
            "http://gatherer.wizards.com/Pages/Card/Details.aspx?name=%s" % \
            re.sub("(.*) // (.*)", r"[\1]+[//]+[\2]", query)
        html = get(html_url).text
        self.dom = parse(html, treebuilder='etree', namespaceHTMLElements=False)

    @property
    def name(self):
        xpath = ".//*[@id='ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_" + \
            "%sRow']/div" % 'name'
        return self.dom.findall(xpath)[1].text.strip().encode('utf-8')

    @property
    def type(self):
        xpath = ".//*[@id='ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_" + \
            "%sRow']/div" % 'type'
        return self.dom.findall(xpath)[1].text.strip().encode('utf-8')

    @property
    def cmc(self):
        xpath = ".//*[@id='ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_" + \
            "%sRow']/div" % 'cmc'
        return self.dom.findall(xpath)[1].text.strip().encode('utf-8')

    @property
    def text(self):
        xpath = ".//*[@id='ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_" + \
            "%sRow']/div/div" % 'text'
        return self.dom.findall(xpath)[0].text.strip().encode('utf-8')

    def __str__(self):
        return "%s | %s | %s | %s" % (self.name, self.type, self.cmc, self.text)

if __name__ == '__main__':
    mde = MtgDeckEditor()
    mde.main()
