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
from random import choice, shuffle
from requests import get
from html5lib import parse

from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas

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
        self.window_curve = self.builder.get_object("window_curve")
        self.window_hand = self.builder.get_object("window_hand")

        self.filechooserdialog_open = \
            self.builder.get_object("filechooserdialog_open")
        self.filechooserdialog_save = \
            self.builder.get_object("filechooserdialog_save")

        self.searchentry = self.builder.get_object("searchentry")
        self.image_card = self.builder.get_object("image_card")
        self.label_card_name_value = self.builder.get_object("label_card_name_value")
        self.label_card_mana_cost_value = \
            self.builder.get_object("label_card_mana_cost_value")
        self.label_card_cmc_value = self.builder.get_object("label_card_cmc_value")
        self.label_card_types_value = \
            self.builder.get_object("label_card_types_value")
        self.label_card_text_value = self.builder.get_object("label_card_text_value")
        self.scrolledwindow_curve = self.builder.get_object('scrolledwindow_curve')

        self.liststore_deck = self.builder.get_object("liststore_deck")
        self.adjustment_card_amount = \
            self.builder.get_object("adjustment_card_amount")

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
        self.label_card_name_value.set_text(card.name)
        self.label_card_cmc_value.set_text(card.cmc)
        self.label_card_types_value.set_text(card.types)

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
                new_amount = amount + self.adjustment_card_amount.get_value()
                self.liststore_deck[row.iter][0] = new_amount
                return
        self.liststore_deck.append([new_amount, card.name])

    def on_button_card_remove_clicked(self, widget, data=None):
        query = self.searchentry.get_text()
        card = get_card(query)
        new_amount = 0
        for row in self.liststore_deck:
            amount = row[0]
            name = row[1]
            if name == card.name:
                new_amount = amount - self.adjustment_card_amount.get_value()
                if new_amount > 0:
                    self.liststore_deck[row.iter][0] = new_amount
                else:
                    self.liststore_deck.remove(row.iter)
                break

    def on_button_curve_clicked(self, widget, data=None):
        fig = Figure(figsize=(5,5), dpi=100)
        ax = fig.add_subplot(111)

        ax.set_title('Mana Curve')

        colors = ['c', 'w', 'u', 'b', 'r', 'g', 'm']

        curve={}
        for color in colors:
            curve[color] = {}

        for cmc in range(15):
            for color in colors:
                curve[color][cmc] = 0
            for row in self.liststore_deck:
                amount = row[0]
                name = row[1]
                card = get_card(name)
                if card.cmc == str(cmc):
                    color = choice(colors)
                    curve[color][cmc] += int(amount)

        kc = [int(cmc) - 0.5 for cmc in curve['c'].keys()]
        vc = curve['c'].values()
        kw = [int(cmc) - 0.5 for cmc in curve['w'].keys()]
        vw = curve['w'].values()
        ku = [int(cmc) - 0.5 for cmc in curve['u'].keys()]
        vu = curve['u'].values()
        kb = [int(cmc) - 0.5 for cmc in curve['b'].keys()]
        vb = curve['b'].values()
        kr = [int(cmc) - 0.5 for cmc in curve['r'].keys()]
        vr = curve['r'].values()
        kg = [int(cmc) - 0.5 for cmc in curve['g'].keys()]
        vg = curve['g'].values()
        km = [int(cmc) - 0.5 for cmc in curve['m'].keys()]
        vm = curve['m'].values()

        # this plot uses tango palette colors
        bc=ax.bar(kc, vc, width=1, color='#c17d11', # “Chocolate”
                  )
        bw=ax.bar(kw, vw, width=1, color='#eeeeec', # “Aluminium Highlight”
                  bottom=vc)
        bu=ax.bar(ku, vu, width=1, color='#3465a4', # “Sky blue”
                  bottom=vw)
        bb=ax.bar(kb, vb, width=1, color='#555753', # “Slate”
                  bottom=vu)
        br=ax.bar(kr, vr, width=1, color='#cc0000', # “Scarlet Red”
                  bottom=vb)
        bg=ax.bar(kg, vg, width=1, color='#73d216', # “Chameleon”
                  bottom=vr)
        bm=ax.bar(km, vm, width=1, color='#c4a000', # “Butter Shadow”
                  bottom=vg)
        ax.plot()

        canvas_curve = FigureCanvas(fig)
        self.scrolledwindow_curve.add_with_viewport(canvas_curve)

        self.window_curve.show_all()

    def on_button_curve_close_clicked(self, widget, data=None):
        self.scrolledwindow_curve.remove(self.scrolledwindow_curve.get_child())
        self.window_curve.hide()

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

    def on_button_save_clicked(self, widget, data=None):
        self.filechooserdialog_save.show()

    def on_button_save_cancel_clicked(self, widget, data=None):
        self.filechooserdialog_save.hide()

    def on_button_save_file_clicked(self, widget, data=None):
        self.filechooserdialog_save.hide()
        filename = self.filechooserdialog_save.get_filename()
        with open(filename, 'w') as deckfile:
            for row in self.liststore_deck:
                amount = row[0]
                name = row[1]
                deckfile.write('%s %s\n' % (amount, name))

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
        for i in range(1,7):
            button = self.builder.get_object("button_hand_mulligan_%s" % i)
            button.hide()
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
    def types(self):
        xpath = ".//*[@id='ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_" + \
            "%sRow']/div" % 'type'
        return self.dom.findall(xpath)[1].text.strip().encode('utf-8')

    @property
    def cmc(self):
        try:
            xpath = \
                ".//*[@id='ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_" + \
                "%sRow']/div" % 'cmc'
            return self.dom.findall(xpath)[1].text.strip().encode('utf-8')
        except IndexError:
            return '0'

    def __str__(self):
        return "%s | %s | %s | %s" % (self.name, self.type, self.cmc, self.text)

if __name__ == '__main__':
    mde = MtgDeckEditor()
    mde.main()
