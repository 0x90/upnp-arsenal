# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>
# Copyright 2014 - Hartmut Goebel <h.goebel@crazy-compilers.com>

import pygtk
pygtk.require("2.0")
import gtk

from coherence import log


class DetailsWidget(log.Loggable):
    logCategory = 'inspector'

    def __init__(self, coherence):
        self.coherence = coherence
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_default_size(500, 460)
        self.window.set_title('Details')
        scroll_window = gtk.ScrolledWindow()
        scroll_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.store = gtk.TreeStore(str, object)
        self.treeview = gtk.TreeView(self.store)
        column = gtk.TreeViewColumn('Name')
        self.treeview.append_column(column)
        text_cell = gtk.CellRendererText()
        column.pack_start(text_cell, False)
        column.set_attributes(text_cell, text=0)
        column = gtk.TreeViewColumn('Value')
        self.treeview.insert_column_with_data_func(
            -1, 'Value', gtk.CellRendererText(), self.celldatamethod)
        text_cell = gtk.CellRendererText()
        column.pack_start(text_cell, True)
        column.set_attributes(text_cell, text=1)

        self.treeview.connect("button_press_event", self.button_action)

        self.clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)

        scroll_window.add(self.treeview)
        self.window.add(scroll_window)

    def celldatamethod(self, column, cell, model, iter):
        value, = model.get(iter, 1)
        if isinstance(value, tuple):
            value = value[0]
        cell.set_property('text', value)

    def refresh(self, object):
        self.store.clear()
        if object == None:
            return
        try:
            for t in object.as_tuples():
                row = self.store.append(None, t)
                try:
                    if isinstance(t[1][2], dict):
                        for k, v in t[1][2].items():
                            self.store.append(row, (k, v))
                except (IndexError, TypeError):
                    pass
        except AttributeError:
            #import traceback
            #print traceback.format_exc()
            pass
        except Exception:
            import traceback
            print traceback.format_exc()

    def open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    def button_action(self, widget, event):
        x = int(event.x)
        y = int(event.y)
        path = self.treeview.get_path_at_pos(x, y)
        if path == None:
            return True
        row_path, column = path[:2]
        if event.button == 3:
            iter = self.store.get_iter(row_path)
            menu = gtk.Menu()
            item = gtk.MenuItem("Copy value")
            value = self.store.get(iter, 1)[0]
            if not isinstance(value, tuple):
                item.connect("activate",
                             lambda w: self.clipboard.set_text(value))
                menu.append(item)
            else:
                item.connect("activate",
                             lambda w: self.clipboard.set_text(value[0]))
                menu.append(item)

                menu.append(gtk.SeparatorMenuItem())
                item = gtk.MenuItem("Copy URL")
                item.connect("activate",
                             lambda w: self.clipboard.set_text(value[1]))
                menu.append(item)

                if (len(value) < 3 or
                    (value[2] == True or isinstance(value[2], dict))):
                    item = gtk.MenuItem("Open URL")
                    item.connect("activate", lambda w: self.open_url(value[1]))
                    menu.append(item)

            menu.show_all()
            menu.popup(None, None, None, event.button, event.time)
            return True

        return False
