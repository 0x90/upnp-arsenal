# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2019 - Frank Scholz <coherence@beebits.net>

import os

import pygtk
pygtk.require("2.0")
import gtk

if __name__ == '__main__':
    from twisted.internet import gtk2reactor
    gtk2reactor.install()
from twisted.internet import reactor
from twisted.internet import task, defer

from coherence import log
from coherence.upnp.core.utils import parse_xml, getPage, means_true, generalise_boolean

from pkg_resources import resource_filename


class IGDWidget(log.Loggable):
    logCategory = 'igd'

    def __init__(self, coherence, device):
        self.coherence = coherence
        self.device = device
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.hide)
        self.window.set_default_size(480, 200)
        try:
            title = 'InternetGatewayDevice %s' % device.get_friendly_name()
        except:
            title = 'InternetGatewayDevice'
        self.window.set_title(title)

        vbox = gtk.VBox(homogeneous=False, spacing=10)
        hbox = gtk.HBox(homogeneous=False, spacing=10)

        text = gtk.Label("<b>Link:</b>")
        text.set_use_markup(True)

        self.link_state_image = gtk.Image()
        icon = resource_filename(__name__, os.path.join('icons', 'red.png'))
        self.link_down_icon = gtk.gdk.pixbuf_new_from_file(icon)
        icon = resource_filename(__name__, os.path.join('icons', 'green.png'))
        self.link_up_icon = gtk.gdk.pixbuf_new_from_file(icon)
        self.link_state_image.set_from_pixbuf(self.link_down_icon)

        hbox.add(text)
        hbox.add(self.link_state_image)

        self.link_type = gtk.Label("<b>Type:</b> unknown (n/a)")
        self.link_type.set_use_markup(True)
        hbox.add(self.link_type)

        vbox.pack_start(hbox, False, False, 2)
        hbox = gtk.HBox(homogeneous=False, spacing=10)
        label = gtk.Label("<b>Uptime:</b>")
        label.set_use_markup(True)
        hbox.add(label)
        self.uptime = gtk.Label("   ")
        self.uptime.set_use_markup(True)
        hbox.add(self.uptime)

        label = gtk.Label("<b>External IP:</b>")
        label.set_use_markup(True)
        hbox.add(label)
        self.external_ip = gtk.Label("   ")
        self.external_ip.set_use_markup(True)
        hbox.add(self.external_ip)

        label = gtk.Label("<b>IN-Bytes:</b>")
        label.set_use_markup(True)
        hbox.add(label)
        self.bytes_in = gtk.Label("   ")
        self.bytes_in.set_use_markup(True)
        hbox.add(self.bytes_in)

        label = gtk.Label("<b>OUT-Bytes:</b>")
        label.set_use_markup(True)
        hbox.add(label)
        self.bytes_out = gtk.Label("   ")
        self.bytes_out.set_use_markup(True)
        hbox.add(self.bytes_out)

        vbox.pack_start(hbox, False, False, 2)

        hbox = gtk.HBox(homogeneous=False, spacing=10)
        label = gtk.Label("<b>Port-Mappings:</b>")
        label.set_use_markup(True)
        hbox.add(label)
        vbox.pack_start(hbox, False, False, 2)

        self.nat_store = gtk.ListStore(str, str, str, str, str, str, str, str, str)
        self.nat_view = gtk.TreeView(self.nat_store)
        self.nat_view.connect("button_press_event", self.button_action)
        i = 0
        for c in ['index', 'enabled', 'protocol', 'remote host', 'external port', 'internal host', 'internal port', 'lease duration', 'description']:
            column = gtk.TreeViewColumn(c)
            self.nat_view.append_column(column)
            text_cell = gtk.CellRendererText()
            column.pack_start(text_cell, True)
            column.add_attribute(text_cell, "text", i)
            i += 1

        vbox.pack_start(self.nat_view, expand=True, fill=True)

        self.window.add(vbox)
        self.window.show_all()

        self.wan_device = None
        self.wan_connection_device = None

        try:
            self.wan_device = self.device.get_embedded_device_by_type('WANDevice')[0]
            print self.wan_device
            service = self.wan_device.get_service_by_type('WANCommonInterfaceConfig')
            service.subscribe_for_variable('PhysicalLinkStatus', callback=self.state_variable_change)
            self.get_traffic_loop = task.LoopingCall(self.get_traffic, service)
            self.get_traffic_loop.start(10, now=True)

        except IndexError:
            pass

        if self.wan_device != None:
            try:
                self.wan_connection_device = self.wan_device.get_embedded_device_by_type('WANConnectionDevice')[0]
                service = self.wan_connection_device.get_service_by_type(['WANIPConnection', 'WANPPPConnection'])
                service.subscribe_for_variable('PortMappingNumberOfEntries', callback=self.state_variable_change)
                service.subscribe_for_variable('ExternalIPAddress', callback=self.state_variable_change)
                self.get_state_loop = task.LoopingCall(self.get_state, service)
                self.get_state_loop.start(10, now=True)
            except IndexError:
                pass

    def button_action(self, widget, event):
        x = int(event.x)
        y = int(event.y)
        path = self.nat_view.get_path_at_pos(x, y)
        if event.button == 3:
            menu = gtk.Menu()
            item = gtk.MenuItem("Add new port-mapping...")
            item.set_sensitive(False)
            menu.append(item)
            if path != None:
                row_path, column, _, _ = path
                iter = self.nat_store.get_iter(row_path)
                selection = self.nat_view.get_selection()
                if not selection.path_is_selected(row_path):
                    self.nat_view.set_cursor(row_path, column, False)
                item = gtk.MenuItem("Modify port-mapping...")
                item.set_sensitive(False)
                menu.append(item)
                item = gtk.MenuItem("Delete port-mapping...")
                item.set_sensitive(True)
                protocol, remote_host, external_port = self.nat_store.get(iter, 2, 3, 4)
                item.connect("activate", self.delete_mapping, protocol, remote_host, external_port)
                menu.append(item)

            menu.show_all()
            menu.popup(None, None, None, event.button, event.time)
            return True

    def delete_mapping(self, widget, protocol, remote_host, external_port):
        service = self.wan_connection_device.get_service_by_type(['WANIPConnection', 'WANPPPConnection'])
        action = service.get_action('DeletePortMapping')
        if action != None:
            d = action.call(NewRemoteHost=remote_host, NewExternalPort=external_port, NewProtocol=protocol)
            d.addCallback(self.handle_result)
            d.addErrback(self.handle_error)

    def hide(self, w, e):
        try:
            self.get_traffic_loop.stop()
        except:
            pass
        try:
            self.get_state_loop.stop()
        except:
            pass
        w.hide()
        return True

    def state_variable_change(self, variable):
        print "%s %r" % (variable.name, variable.value)
        if variable.name == "PhysicalLinkStatus":
            if variable.value.lower() == 'up':
                self.link_state_image.set_from_pixbuf(self.link_up_icon)
            else:
                self.link_state_image.set_from_pixbuf(self.link_down_icon)

            def request_cb(r):
                #print r
                self.link_type.set_markup("<b>Type:</b> %s (%s/%s)" % (r['NewWANAccessType'], r['NewLayer1DownstreamMaxBitRate'], r['NewLayer1UpstreamMaxBitRate']))

            action = variable.service.get_action('GetCommonLinkProperties')
            d = action.call()
            d.addCallback(request_cb)
            d.addErrback(self.handle_error)

        elif variable.name == "PortMappingNumberOfEntries":
            self.nat_store.clear()
            if type(variable.value) == int and variable.value > 0:
                l = []
                for i in range(variable.value):
                    action = variable.service.get_action('GetGenericPortMappingEntry')
                    d = action.call(NewPortMappingIndex=i)

                    def add_index(r, index):
                        r['NewPortMappingIndex'] = index
                        return r
                    d.addCallback(add_index, i + 1)
                    d.addErrback(self.handle_error)
                    l.append(d)

                def request_cb(r, last_updated_timestamp, v):
                    #print r
                    #print last_updated_timestamp == v.last_time_touched,last_updated_timestamp,v.last_time_touched
                    if last_updated_timestamp == v.last_time_touched:
                        mappings = [m[1] for m in r if m[0] == True]
                        mappings.sort(cmp=lambda x, y: cmp(x['NewPortMappingIndex'], y['NewPortMappingIndex']))
                        for mapping in mappings:
                            #print mapping
                            self.nat_store.append([mapping['NewPortMappingIndex'],
                                                   mapping['NewEnabled'],
                                                   mapping['NewProtocol'],
                                                   mapping['NewRemoteHost'],
                                                   mapping['NewExternalPort'],
                                                   mapping['NewInternalClient'],
                                                   mapping['NewInternalPort'],
                                                   mapping['NewLeaseDuration'],
                                                   mapping['NewPortMappingDescription']
                                                   ])

                dl = defer.DeferredList(l)
                dl.addCallback(request_cb, variable.last_time_touched, variable)
                dl.addErrback(self.handle_error)

        elif variable.name == "ExternalIPAddress":
            self.external_ip.set_markup(variable.value)

    def get_traffic(self, service):
        def request_cb(r, item, argument):
            item.set_markup(r[argument])

        action = service.get_action('GetTotalBytesReceived')
        if action != None:
            d = action.call()
            d.addCallback(request_cb, self.bytes_in, 'NewTotalBytesReceived')
            d.addErrback(self.handle_error)
        action = service.get_action('GetTotalBytesSent')
        if action != None:
            d = action.call()
            d.addCallback(request_cb, self.bytes_out, 'NewTotalBytesSent')
            d.addErrback(self.handle_error)

    def get_state(self, service):
        def request_cb(r):
            #print r
            self.uptime.set_markup(r['NewUptime'])

        action = service.get_action('GetStatusInfo')
        if action != None:
            d = action.call()
            d.addCallback(request_cb)
            d.addErrback(self.handle_error)

    def handle_error(self, e):
        print 'we have an error', e
        return e

    def handle_result(self, r):
        print "done", r
        return r

if __name__ == '__main__':

    IGD.hide = lambda x, y, z: reactor.stop()
    i = IGDWidget(None, None)
    reactor.run()
