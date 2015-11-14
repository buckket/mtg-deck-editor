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

from gi.repository import GLib, Gio, Gtk, GObject
from gi.repository.GdkPixbuf import Pixbuf

from operator import add
from random import shuffle
from requests import get
from html5lib import parse

from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas

import json
import os
import re
import threading
GObject.threads_init()

try:
    from requests_cache import install_cache
    install_cache('mtg-deck-editor-cache')
except ImportError:
    pass

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
        self.recentmanager = Gtk.RecentManager.get_default()

        self.progressbar = self.builder.get_object("progressbar")
        self.treeview_deck = self.builder.get_object("treeview_deck")

        self.button_curve = self.builder.get_object("button_curve")
        self.button_hand = self.builder.get_object("button_hand")

        self.searchentry = self.builder.get_object("searchentry")

        # The following code is a workaround for a GtkBuilder bug.
        # See <https://bugzilla.redhat.com/show_bug.cgi?id=907946>
        entrycompletion_search = self.builder.get_object("entrycompletion_search")
        entrycompletion_search.set_text_column(0)

        self.spinner_search = self.builder.get_object("spinner_search")
        self.image_card = self.builder.get_object("image_card")
        self.scrolledwindow_curve = self.builder.get_object('scrolledwindow_curve')
        self.buttonbox_add_remove = self.builder.get_object("buttonbox_add_remove")

        self.liststore_deck = self.builder.get_object("liststore_deck")
        self.liststore_search = self.builder.get_object("liststore_search")
        self.adjustment_card_amount = \
            self.builder.get_object("adjustment_card_amount")

    def main(self):
        self.window_main.show_all()
        Gtk.main()

    def clear(self):
        for row in self.liststore_deck:
            self.liststore_deck.remove(row.iter)

    def add_card(self, query, amount, total_cards):
        def add_card_async(query, amount, total_cards):
            def add_card_callback(name, amount, total_cards):
                self.liststore_deck.append([amount, name])
                current_progress = self.progressbar.get_fraction()
                self.progressbar.set_fraction(current_progress + (1.0/total_cards))
                if self.progressbar.get_fraction() > 0.999:
                    self.progressbar.hide()
                    self.treeview_deck.set_sensitive(True)
                return False

            card = get_card(query)
            GLib.idle_add(add_card_callback, card.name, amount, total_cards)
            return False

        self.treeview_deck.set_sensitive(False)
        self.progressbar.set_fraction(0)
        self.progressbar.show()
        thread = threading.Thread(target=add_card_async,
                                  args=(query,amount,total_cards))
        thread.daemon = True
        thread.start()

    def add_entrycompletion(self, query):
        def callback(source_object, result, user_data):
            success, content, etag = source_object.load_contents_finish(result)
            names = [x['name'] for x in json.loads(content)]
            for name in names:
                if name not in [row[0] for row in self.liststore_search]:
                    self.liststore_search.append([name])

        self.cancellable = Gio.Cancellable()
        typeahead_url = 'https://api.deckbrew.com/mtg/cards/typeahead?q=%s' % query
        stream = Gio.File.new_for_uri(typeahead_url)
        stream.load_contents_async(self.cancellable, callback, None)

    def display_card(self, query):
        def display_card_async(query):
            def display_card_callback(pixbuf):
                self.image_card.set_from_pixbuf(pixbuf)
                self.buttonbox_add_remove.set_sensitive(True)
                self.searchentry.set_sensitive(True)
                self.spinner_search.stop()
                self.spinner_search.hide()
                self.image_card.show()
                return False

            card = get_card(query)
            GLib.idle_add(display_card_callback, card.pixbuf)

        self.searchentry.set_sensitive(False)
        self.buttonbox_add_remove.set_sensitive(False)
        self.spinner_search.start()
        self.spinner_search.show()
        self.image_card.hide()
        thread = threading.Thread(target=display_card_async, args=(query,))
        thread.daemon = True
        thread.start()

    def on_window_main_destroy(self, widget, data=None):
        Gtk.main_quit()

    def on_liststore_deck_row_changed(self, widget, path=None, iterator=None):
        total_cards = sum([row[0] for row in self.liststore_deck])
        if total_cards == 0:
            self.button_curve.set_sensitive(False)
        else:
            self.button_curve.set_sensitive(True)
        if total_cards < 7:
            self.button_hand.set_sensitive(False)
        else:
            self.button_hand.set_sensitive(True)

    def on_liststore_deck_row_deleted(self, widget, data=None):
        self.on_liststore_deck_row_changed(widget)

    def on_liststore_deck_row_inserted(self, widget, path=None, iterator=None):
        self.on_liststore_deck_row_changed(widget, path, iterator)

    def on_searchentry_activate(self, widget, data=None):
        query = widget.get_text()
        self.display_card(query)

    def on_searchentry_search_changed(self, widget, data=None):
        query = widget.get_text()
        self.add_entrycompletion(query)

    def on_button_new_clicked(self, widget, data=None):
        self.clear()

    def on_button_card_add_clicked(self, widget, data=None):
        query = self.searchentry.get_text()
        self.display_card(query)
        new_amount = self.adjustment_card_amount.get_value()
        for row in self.liststore_deck:
            amount = row[0]
            name = row[1]
            if name == query:
                new_amount = amount + self.adjustment_card_amount.get_value()
                self.liststore_deck[row.iter][0] = new_amount
                return
        self.liststore_deck.append([new_amount, query])

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

        ax.set_xlim([0,16])
        ax.set_xticks(range(17))

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
                if card.cmc_lower == cmc:
                    if 'Land' in card.types:
                        continue
                    color = card.color
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
        bottom = [0]*len(vc)
        if sum(vc) > 0:
            bc=ax.bar(kc, vc, width=1, color='#c17d11', # “Chocolate”
                      bottom=bottom, label='Colorless')
            bottom=map(add, bottom, vc)
        if sum(vw) > 0:
            bw=ax.bar(kw, vw, width=1, color='#d3d7cf', # “Aluminium”
                      bottom=bottom, label='White')
            bottom=map(add, bottom, vw)
        if sum(vu) > 0:
            bu=ax.bar(ku, vu, width=1, color='#3465a4', # “Sky blue”
                      bottom=bottom, label='Blue')
            bottom=map(add, bottom, vu)
        if sum(vb) > 0:
            bb=ax.bar(kb, vb, width=1, color='#555753', # “Slate”
                      bottom=bottom, label='Black')
            bottom=map(add, bottom, vb)
        if sum(vr) > 0:
            br=ax.bar(kr, vr, width=1, color='#cc0000', # “Scarlet Red”
                      bottom=bottom, label='Red')
            bottom=map(add, bottom, vr)
        if sum(vg) > 0:
            bg=ax.bar(kg, vg, width=1, color='#73d216', # “Chameleon”
                      bottom=bottom, label='Green')
            bottom=map(add, bottom, vg)
        if sum(vm) > 0:
            bm=ax.bar(km, vm, width=1, color='#c4a000', # “Butter Shadow”
                      bottom=bottom, label='Multicolor')
        ax.plot()
        ax.legend()

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

    def on_filechooserdialog_open_file_activated(self, widget, data=None):
        self.on_button_open_file_clicked(widget)

    def on_filechooserdialog_open_delete_event(self, widget, data=None):
        self.filechooserdialog_open.hide()
        return True

    def on_button_open_file_clicked(self, widget, data=None):
        self.filechooserdialog_open.hide()
        filename = self.filechooserdialog_open.get_filename()
        self.recentmanager.add_item(filename)
        self.clear()
        with open(filename) as deckfile:
            data = deckfile.read()
            total_cards = len(data.split('\n')) - 1
            for line in data.split('\n'):
                tokens = line.split(' ')
                try:
                    amount = int(tokens[0])
                except ValueError:
                    continue
                name = ' '.join(tokens[1:])
                if name != '':
                    self.add_card(name, amount, total_cards)

    def on_button_save_clicked(self, widget, data=None):
        self.filechooserdialog_save.show()

    def on_button_save_cancel_clicked(self, widget, data=None):
        self.filechooserdialog_save.hide()

    def on_filechooserdialog_save_delete_event(self, widget, data=None):
        self.filechooserdialog_save.hide()
        return True

    def on_button_save_file_clicked(self, widget, data=None):
        self.filechooserdialog_save.hide()
        filename = self.filechooserdialog_save.get_filename()
        self.recentmanager.add_item(filename)
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

    def on_entrycompletion_search_action_activated(self, widget, data=None):
        self.searchentry.activate()

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

class Card:
    def __init__(self, query):
        self.query = query

        image_url = \
            "http://gatherer.wizards.com/Handlers/Image.ashx?type=card&name=%s" % \
            self.query
        # rotate split cards
        if '//' in self.query:
            image_url= '%s&options=rotate90' % image_url
        image_raw = get(image_url).content
        input_stream = Gio.MemoryInputStream.new_from_data(image_raw, None)
        self.pixbuf = Pixbuf.new_from_stream(input_stream, None)

        # handle split cards
        html_url = \
            "http://gatherer.wizards.com/Pages/Card/Details.aspx?name=%s" % \
            re.sub("(.*) // (.*)", r"[\1]+[//]+[\2]", self.query)
        html = get(html_url).text
        self.dom = parse(html, treebuilder='etree', namespaceHTMLElements=False)

    @property
    def name(self):
        try:
            xpath = \
                ".//*[@id='ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_" + \
                "%sRow']/div" % 'name'
            return self.dom.findall(xpath)[1].text.strip().encode('utf-8')
        except IndexError:
            return self.query

    @property
    def mana_cost(self):
        xpath =".//*[@id='ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_" + \
            "%sRow']/div/img" % 'mana'
        return [e.attrib['alt'] for e in self.dom.findall(xpath)]

    @property
    def types(self):
        try:
            xpath = \
                ".//*[@id='ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_" + \
                "%sRow']/div" % 'type'
            return self.dom.findall(xpath)[1].text.strip().encode('utf-8')
        except IndexError:
            return 'unknown'

    @property
    def cmc(self):
        try:
            xpath = \
                ".//*[@id='ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_" + \
                "%sRow']/div" % 'cmc'
            return self.dom.findall(xpath)[1].text.strip().encode('utf-8')
        except IndexError:
            return '0'

    @property
    def cmc_lower(self):
        cmc_lower = 0
        for s in self.mana_cost:
            try:
                cmc_lower += int(s)
            except ValueError:
                if not s.startswith('Phyrexian'):
                    cmc_lower += 1
        return cmc_lower

    @property
    def color(self):
        # colors = ['c', 'w', 'u', 'b', 'r', 'g', 'm']
        color = 'c' # colorless
        for s in self.mana_cost:
            if s in (u'White', u'Two or White', u'Phyrexian White'):
                if color in ('c', 'w'):
                    color = 'w'
                else:
                    color = 'm'
            if s in (u'Blue', u'Two or Blue', u'Phyrexian Blue'):
                if color in ('c', 'u'):
                    color = 'u'
                else:
                    color = 'm'
            if s in (u'Black', u'Two or Black', u'Phyrexian Black'):
                if color in ('c', 'b'):
                    color = 'b'
                else:
                    color = 'm'
            if s in (u'Red', u'Two or Red', u'Phyrexian Red'):
                if color in ('c', 'r'):
                    color = 'r'
                else:
                    color = 'm'
            if s in (u'Green', u'Two or Green', u'Phyrexian Green'):
                if color in ('c', 'g'):
                    color = 'g'
                else:
                    color = 'm'
            # hybrid mana
            if s in (
                u'White or Blue',
                u'White or Black'
                u'Blue or Black',
                u'Blue or Red',
                u'Black or Red',
                u'Black or Green',
                u'Red or White',
                u'Red or Green',
                u'Green or Blue',
                u'Green or White',
                ):
                color = 'm'
        return color

    def __str__(self):
        return "%s | %s | %s | %s" % (self.name, self.type, self.cmc, self.text)

if __name__ == '__main__':
    mde = MtgDeckEditor()
    mde.main()
