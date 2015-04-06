# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>
# Copyright 2014 - Hartmut Goebel <h.goebel@crazy-compilers.com>

import time

import pygtk
pygtk.require("2.0")
import gtk

from coherence import log


class LogWidget(log.Loggable):
    logCategory = 'inspector'

    def __init__(self, coherence, max_lines=500):
        self.coherence = coherence
        self.max_lines = max_lines
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_default_size(500, 400)
        self.window.set_title('Log')
        scroll_window = gtk.ScrolledWindow()
        scroll_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.store = gtk.ListStore(str, str, str, str)
        self.treeview = gtk.TreeView(self.store)

        for i, title in enumerate(('Time', '','Host', '')):
            column = gtk.TreeViewColumn(title)
            self.treeview.append_column(column)
            text_cell = gtk.CellRendererText()
            column.pack_start(text_cell, False)
            column.set_attributes(text_cell, text=i)

        scroll_window.add_with_viewport(self.treeview)
        #self.treeview.set_fixed_height_mode(True)
        self.window.add(scroll_window)
        self.coherence.connect(self.append, 'Coherence.UPnP.Log')

    def append(self, module, host, txt):
        if len(self.store) >= 500:
            del self.store[0]

        timestamp = time.strftime("%H:%M:%S")
        self.store.insert(0, (timestamp, module, host, txt))
