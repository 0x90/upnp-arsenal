# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>
# Copyright 2014 - Hartmut Goebel <h.goebel@crazy-compilers.com>

import time

import pygtk
pygtk.require("2.0")
import gtk

from twisted.internet import reactor

from coherence import log


class EventsWidget(log.Loggable):
    logCategory = 'inspector'

    def __init__(self, coherence, max_lines=500):
        self.coherence = coherence
        self.max_lines = max_lines
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_default_size(500, 400)
        self.window.set_title('Events')
        scroll_window = gtk.ScrolledWindow()
        scroll_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.store = gtk.ListStore(str, str, str, str, str, str)
        self.treeview = gtk.TreeView(self.store)

        for i, title in enumerate(
            ('Time', 'Device','Service', 'Variable', 'Value')):
            column = gtk.TreeViewColumn(title)
            self.treeview.append_column(column)
            text_cell = gtk.CellRendererText()
            column.pack_start(text_cell, False)
            column.set_attributes(text_cell, text=i)

        scroll_window.add_with_viewport(self.treeview)
        #self.treeview.set_fixed_height_mode(True)
        self.window.add(scroll_window)

        self.treeview.connect("button_press_event", self.button_action)

        self.coherence.connect(self.append,
                               'Coherence.UPnP.DeviceClient.Service.Event.processed')

    def append(self, service, event):
        if len(self.store) >= 500:
            del self.store[0]

        timestamp = time.strftime("%H:%M:%S")
        _, _, _, service_class, version = service.service_type.split(':')
        self.store.insert(0, (timestamp, service.device.friendly_name,
                              service_class, event[0], event[1], event[2]))

    def button_action(self, widget, event):
        x = int(event.x)
        y = int(event.y)
        path = self.treeview.get_path_at_pos(x, y)
        if path == None:
            return True
        row_path, column, _, _ = path
        if event.button == 3:
            clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
            iter = self.store.get_iter(row_path)
            menu = gtk.Menu()
            item = gtk.MenuItem("Copy value")
            value, = self.store.get(iter, 4)
            item.connect("activate", lambda w: clipboard.set_text(value))
            menu.append(item)

            item = gtk.MenuItem("Copy raw event XML")
            raw, = self.store.get(iter, 5)
            try:
                from coherence.extern.et import ET, indent, parse_xml
                xml = parse_xml(raw)
                xml = xml.getroot()
                indent(xml, 0)
                raw = ET.tostring(xml, encoding='utf-8')
            except:
                import traceback
                print traceback.format_exc()

            item.connect("activate", lambda w: clipboard.set_text(raw))
            menu.append(item)

            menu.show_all()
            menu.popup(None, None, None, event.button, event.time)
            return True

        return False
