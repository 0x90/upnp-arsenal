# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2008 Frank Scholz <coherence@beebits.net>
# Copyright 2014 - Hartmut Goebel <h.goebel@crazy-compilers.com>

import pygtk
pygtk.require("2.0")
import gtk

from twisted.internet import reactor

from coherence.base import Coherence
from coherence.upnp.devices.control_point import ControlPoint
from coherence.upnp.core.utils import means_true

from coherence import log

from about import AboutWidget
from details import DetailsWidget
from events import EventsWidget
from log import LogWidget
from devices import DevicesWidget, OBJECT_COLUMN
from ._resources import _geticon_path


class Inspector(log.Loggable):
    logCategory = 'inspector'

    def __init__(self, logfile=None):
        config = {'logmode': 'none',
                  'logfile': logfile}
        self.coherence = Coherence(config)
        self.controlpoint = ControlPoint(self.coherence, auto_client=[])
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        agr = gtk.AccelGroup()
        window.add_accel_group(agr)

        window.connect("delete_event", lambda x, y: reactor.stop())
        window.set_default_size(350, 700)
        window.set_title('UPnP Inspector')
        icon = _geticon_path('inspector-icon.png')
        gtk.window_set_default_icon_from_file(icon)

        vbox = gtk.VBox(homogeneous=False, spacing=0)
        menu_bar = gtk.MenuBar()
        menu = gtk.Menu()
        refresh_item = gtk.MenuItem("Rediscover Devices")
        refresh_item.connect("activate", self.refresh_devices)
        menu.append(refresh_item)
        menu.append(gtk.SeparatorMenuItem())

        quit_item = gtk.ImageMenuItem(gtk.STOCK_QUIT, agr)
        key, mod = gtk.accelerator_parse("<Control>Q")
        quit_item.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        menu.append(quit_item)
        quit_item.connect("activate", lambda x: reactor.stop())

        file_menu = gtk.MenuItem("File")
        file_menu.set_submenu(menu)
        menu_bar.append(file_menu)

        menu = gtk.Menu()
        self.show_details_item = gtk.CheckMenuItem("Show details")
        menu.append(self.show_details_item)
        self.show_details_item.connect("activate", self.show_details_widget,
                                       "view.details")
        self.show_events_item = gtk.CheckMenuItem("Show events")
        menu.append(self.show_events_item)
        self.show_events_item.connect("activate", self.show_events_widget,
                                      "view.events")
        self.show_log_item = gtk.CheckMenuItem("Show global log")
        menu.append(self.show_log_item)
        self.show_log_item.connect("activate", self.show_log_widget, "view.log")
        #self.show_log_item.set_sensitive(False)
        view_menu = gtk.MenuItem("View")
        view_menu.set_submenu(menu)
        menu_bar.append(view_menu)

        test_menu = gtk.MenuItem("Test")
        test_menu.set_sensitive(False)
        #test_menu.set_submenu(menu)
        menu_bar.append(test_menu)

        menu = gtk.Menu()
        item = gtk.MenuItem("Info...")
        menu.append(item)
        item.connect("activate", self.show_about_widget, "help.info")
        help_menu = gtk.MenuItem("Help")
        help_menu.set_submenu(menu)
        menu_bar.append(help_menu)

        vbox.pack_start(menu_bar, False, False, 2)

        self.device_tree = DevicesWidget(self.coherence)
        self.device_tree.cb_item_left_click = self.show_details
        vbox.pack_start(self.device_tree.window, True, True, 0)
        window.add(vbox)
        window.show_all()

        self.events_widget = EventsWidget(self.coherence)
        self.events_widget.window.connect('delete_event',
                                          self.hide_events_widget)
        self.details_widget = DetailsWidget(self.coherence)
        self.details_widget.window.connect('delete_event',
                                           self.hide_details_widget)
        self.log_widget = LogWidget(self.coherence)
        self.log_widget.window.connect('delete_event', self.hide_log_widget)

    def show_details(self, widget, event):
        #print "show_details", widget
        selection = widget.get_selection()
        (model, iter) = selection.get_selected()
        #print model, iter
        try:
            object, = model.get(iter, OBJECT_COLUMN)
            self.details_widget.refresh(object)
        except TypeError:
            pass

    def show_details_widget(self, w, hint):
        #print "show_details_widget", w, w.get_active()
        if w.get_active() == True:
            self.details_widget.window.show_all()
        else:
            self.details_widget.window.hide()

    def hide_details_widget(self, w, e):
        #print "hide_details_widget", w, e
        self.details_widget.window.hide()
        self.show_details_item.set_active(False)
        return True

    def show_events_widget(self, w, hint):
        if w.get_active() == True:
            self.events_widget.window.show_all()
        else:
            self.events_widget.window.hide()

    def hide_events_widget(self, w, e):
        self.events_widget.window.hide()
        self.show_events_item.set_active(False)
        return True

    def show_log_widget(self, w, hint):
        if w.get_active() == True:
            self.log_widget.window.show_all()
        else:
            self.log_widget.window.hide()

    def hide_log_widget(self, w, e):
        self.log_widget.window.hide()
        self.show_log_item.set_active(False)
        return True

    def refresh_devices(self, w):
        """ FIXME - this is something that's actually useful in the main Coherence class too
        """
        for item in self.coherence.ssdp_server.known.values():
            if item['MANIFESTATION'] == 'remote':
                self.coherence.ssdp_server.unRegister(item['USN'])
        self.coherence.msearch.double_discover()

    def show_about_widget(self, w, hint):
        AboutWidget()
