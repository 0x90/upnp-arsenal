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

from coherence.base import Coherence
from coherence.upnp.core.utils import means_true

from coherence import log

from ._resources import _geticon

# gtk store defines
TYPE_COLUMN = 0
NAME_COLUMN = 1
UDN_COLUMN = 2
ICON_COLUMN = 3
OBJECT_COLUMN = 4

DEVICE = 0
SERVICE = 1
VARIABLE = 2
ACTION = 3
ARGUMENT = 4

def device_type(object):
    if object is None:
        return None
    return object.get_device_type().split(':')[3].lower()

class DevicesWidget(log.Loggable):
    logCategory = 'inspector'

    def __init__(self, coherence):
        self.coherence = coherence

        self.cb_item_dbl_click = None
        self.cb_item_left_click = None
        self.cb_item_right_click = None
        self.cb_resource_chooser = None

        self.build_ui()
        self.init_controlpoint()

    def build_ui(self):
        self.window = gtk.ScrolledWindow()
        self.window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.icons = {}
        self.icons['device'] = _geticon('upnp-device.png')
        self.icons['mediaserver'] = _geticon('network-server.png')
        self.icons['mediarenderer'] = _geticon('media-renderer.png')
        self.icons['binarylight'] = _geticon('network-light.png')
        self.icons['dimmablelight'] = self.icons['binarylight']
        self.icons['digitalsecuritycamera'] = _geticon('camera-web.png')
        self.icons['printer'] = _geticon('printer.png')

        self.folder_icon = _geticon('folder.png')
        self.service_icon = _geticon('upnp-service.png')
        self.action_icon = _geticon('upnp-action.png')
        self.action_arg_in_icon = _geticon('upnp-action-arg-in.png')
        self.action_arg_out_icon = _geticon('upnp-action-arg-out.png')
        self.state_variable_icon = _geticon('upnp-state-variable.png')

        self.store = gtk.TreeStore(int,  # 0: type
                                   str,  # 1: name
                                   str,  # 2: device udn
                                   gtk.gdk.Pixbuf,
                                   object
                                )

        self.treeview = gtk.TreeView(self.store)
        self.column = gtk.TreeViewColumn('Devices')
        self.treeview.append_column(self.column)

        # create a CellRenderers to render the data
        icon_cell = gtk.CellRendererPixbuf()
        text_cell = gtk.CellRendererText()

        self.column.pack_start(icon_cell, False)
        self.column.pack_start(text_cell, True)

        self.column.set_attributes(text_cell, text=1)
        self.column.add_attribute(icon_cell, "pixbuf", 3)
        #self.column.set_cell_data_func(self.cellpb, get_icon)

        self.treeview.connect("button_press_event", self.button_action)
        self.treeview.connect("row-activated", self.activated)
        self.treeview.connect("move_cursor", self.moved_cursor)

        gtk.binding_entry_add_signal(self.treeview, gtk.keysyms.Left, 0,
                                     "expand-collapse-cursor-row",
                                     bool, False, bool, False, bool, False)
        gtk.binding_entry_add_signal(self.treeview, gtk.keysyms.Right, 0,
                                     "expand-collapse-cursor-row",
                                     bool, False, bool, True, bool, False)

        selection = self.treeview.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)

        self.window.add(self.treeview)

        self.windows = {}

    def _build_run_action_box(self, object, id, row_path):
        window = gtk.Window()
        window.set_default_size(350, 300)
        window.set_title('Invoke Action %s' % object.name)
        window.connect("delete_event", self.deactivate, id)

        def build_label(icon, label):
            hbox = gtk.HBox(homogeneous=False, spacing=10)
            image = gtk.Image()
            image.set_from_pixbuf(icon)
            hbox.pack_start(image, False, False, 2)
            text = gtk.Label(label)
            hbox.pack_start(text, False, False, 2)
            return hbox

        def build_button(label):
            hbox = gtk.HBox(homogeneous=False, spacing=10)
            image = gtk.Image()
            image.set_from_pixbuf(self.action_icon)
            hbox.pack_start(image, False, False, 2)
            text = gtk.Label(label)
            hbox.pack_start(text, False, False, 2)
            button = gtk.Button()
            button.set_flags(gtk.CAN_DEFAULT)
            button.add(hbox)

            return button

        def build_arguments(action, direction):
            text = gtk.Label("<b>'%s' arguments:</b>'" % direction)
            text.set_use_markup(True)
            hbox = gtk.HBox(homogeneous=False, spacing=10)
            hbox.pack_start(text, False, False, 2)
            vbox = gtk.VBox(homogeneous=False, spacing=10)
            vbox.pack_start(hbox, False, False, 2)
            row = 0
            if direction == 'in':
                arguments = object.get_in_arguments()
            else:
                arguments = object.get_out_arguments()
            table = gtk.Table(rows=len(arguments), columns=2,
                              homogeneous=False)
            entries = {}
            for argument in arguments:
                variable = action.service.get_state_variable(
                    argument.state_variable)
                name = gtk.Label(argument.name + ':')
                name.set_alignment(0, 0)
                #hbox = gtk.HBox(homogeneous=False, spacing=2)
                #hbox.pack_start(name,False,False,2)
                table.attach(name, 0, 1, row, row + 1, gtk.SHRINK)
                if variable.data_type == 'boolean':
                    entry = gtk.CheckButton()
                    if direction == 'in':
                        entries[argument.name] = entry.get_active
                    else:
                        entry.set_sensitive(False)
                        entries[argument.name] = (variable.data_type, entry.set_active)
                elif variable.data_type == 'string':
                    if direction == 'in' and len(variable.allowed_values) > 0:
                        store = gtk.ListStore(str)
                        for value in variable.allowed_values:
                            store.append((value, ))
                        entry = gtk.ComboBox()
                        text_cell = gtk.CellRendererText()
                        entry.pack_start(text_cell, True)
                        entry.set_attributes(text_cell, text=0)
                        entry.set_model(store)
                        entry.set_active(0)
                        entries[argument.name] = (entry.get_active, entry.get_model)
                    else:
                        if direction == 'in':
                            entry = gtk.Entry(max=0)
                            entries[argument.name] = entry.get_text
                        else:
                            entry = gtk.ScrolledWindow()
                            entry.set_border_width(1)
                            entry.set_shadow_type(gtk.SHADOW_ETCHED_IN)
                            entry.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
                            textview = gtk.TextView()
                            textview.set_editable(False)
                            textview.set_wrap_mode(gtk.WRAP_WORD)
                            entry.add(textview)
                            entries[argument.name] = ('text', textview)
                else:
                    if direction == 'out':
                        entry = gtk.Entry(max=0)
                        entry.set_editable(False)
                        entries[argument.name] = (variable.data_type, entry.set_text)
                    else:
                        adj = gtk.Adjustment(0, 0, 4294967296, 1.0, 50.0, 0.0)
                        entry = gtk.SpinButton(adj, 0, 0)
                        entry.set_numeric(True)
                        entry.set_digits(0)
                        entries[argument.name] = entry.get_value_as_int

                table.attach(entry, 1, 2, row, row + 1, gtk.FILL | gtk.EXPAND, gtk.FILL | gtk.EXPAND)
                row += 1
            #hbox = gtk.HBox(homogeneous=False, spacing=10)
            #hbox.pack_start(table,False,False,2)
            #hbox.show()
            vbox.pack_start(table, False, False, 2)
            return vbox, entries

        vbox = gtk.VBox(homogeneous=False, spacing=10)
        vbox.pack_start(build_label(self.store[row_path[0]][ICON_COLUMN],
                                    self.store[row_path[0]][NAME_COLUMN]),
                        False, False, 2)
        vbox.pack_start(build_label(self.service_icon,
                                    self.store[row_path[0],
                                               row_path[1]][NAME_COLUMN]),
                        False, False, 2)
        vbox.pack_start(build_label(self.action_icon, object.name),
                        False, False, 2)
        hbox = gtk.HBox(homogeneous=False, spacing=10)
        hbox.pack_start(vbox, False, False, 2)
        button = build_button('Invoke')
        hbox.pack_end(button, False, False, 20)
        vbox = gtk.VBox(homogeneous=False, spacing=10)
        vbox.pack_start(hbox, False, False, 2)
        in_entries = {}
        out_entries = {}
        if len(object.get_in_arguments()) > 0:
            box, in_entries = build_arguments(object, 'in')
            vbox.pack_start(box, False, False, 2)
        if len(object.get_out_arguments()) > 0:
            box, out_entries = build_arguments(object, 'out')
            vbox.pack_start(box, False, False, 2)
        window.add(vbox)

        status_bar = gtk.Statusbar()
        context_id = status_bar.get_context_id("Action Statusbar")
        vbox.pack_end(status_bar, False, False, 2)

        button.connect('clicked', self.call_action, object,
                       in_entries, out_entries, status_bar)

        window.show_all()
        self.windows[id] = window

    def activated(self, view, row_path, column):
        iter = self.store.get_iter(row_path)
        if iter:
            type, object = self.store.get(iter, TYPE_COLUMN, OBJECT_COLUMN)
            if type == ACTION:
                id = '@'.join((object.service.device.get_usn(),
                               object.service.service_type,
                               object.name))
                try:
                    self.windows[id].show()
                except:
                    self._build_run_action_box(object, id, row_path)
            elif type == DEVICE:
                devtype = device_type(object)
                if devtype == 'mediaserver':
                    self.mediaserver_browse(None, object)
                elif devtype == 'mediarenderer':
                    self.mediarenderer_control(None, object)
                elif devtype == 'internetgatewaydevice':
                    self.igd_control(None, object)
            else:
                if view.row_expanded(row_path):
                    view.collapse_row(row_path)
                else:
                    view.expand_row(row_path, False)

    def deactivate(self, window, event, id):
        #print "deactivate",id
        del self.windows[id]

    def button_action(self, widget, event):
        x = int(event.x)
        y = int(event.y)
        path = self.treeview.get_path_at_pos(x, y)
        if path == None:
            return True
        row_path, column, _, _ = path
        if event.button == 3:
            if self.cb_item_right_click != None:
                return self.cb_item_right_click(widget, event)
            else:
                iter = self.store.get_iter(row_path)
                type, object = self.store.get(iter, TYPE_COLUMN, OBJECT_COLUMN)
                if type == DEVICE:
                    menu = gtk.Menu()
                    item = gtk.CheckMenuItem("Show events")
                    item.set_sensitive(False)
                    menu.append(item)
                    item = gtk.CheckMenuItem("Show log")
                    item.set_sensitive(False)
                    menu.append(item)
                    menu.append(gtk.SeparatorMenuItem())
                    item = gtk.MenuItem("Extract device and service descriptions...")
                    item.connect("activate", self.extract_descriptions, object)
                    menu.append(item)
                    menu.append(gtk.SeparatorMenuItem())
                    item = gtk.MenuItem("Test device...")
                    item.set_sensitive(False)
                    menu.append(item)
                    devtype = device_type(object)
                    if devtype == 'mediaserver':
                        menu.append(gtk.SeparatorMenuItem())
                        item = gtk.MenuItem("Browse MediaServer...")
                        item.connect("activate", self.mediaserver_browse, object)
                        menu.append(item)
                    elif devtype == 'mediarenderer':
                        menu.append(gtk.SeparatorMenuItem())
                        item = gtk.MenuItem("Control MediaRendererer...")
                        item.connect("activate", self.mediarenderer_control, object)
                        menu.append(item)
                    elif devtype == 'internetgatewaydevice':
                        menu.append(gtk.SeparatorMenuItem())
                        item = gtk.MenuItem("control InternetGatewayDevice")
                        item.connect("activate", self.igd_control, object)
                        menu.append(item)
                    menu.show_all()
                    menu.popup(None, None, None, event.button, event.time)
                    return True
                elif type == SERVICE:
                    menu = gtk.Menu()
                    item = gtk.CheckMenuItem("Show events")
                    item.set_sensitive(False)
                    menu.append(item)
                    item = gtk.CheckMenuItem("Show log")
                    item.set_sensitive(False)
                    menu.append(item)
                    menu.show_all()
                    menu.popup(None, None, None, event.button, event.time)
                    return True
                return False
        elif (event.button == 1 and
            self.cb_item_left_click != None):
            reactor.callLater(0.1, self.cb_item_left_click, widget, event)
            return False
        return 0

    def extract_descriptions(self, widget, device):
        print "extract xml descriptions", widget, device
        from extract import Extract
        id = '@'.join((device.get_usn(), 'DeviceXMlExtract'))
        try:
            self.windows[id].show()
        except:
            ui = Extract(device)
            self.windows[id] = ui.window

    def moved_cursor(self, widget, step, count):
        reactor.callLater(0.1, self.cb_item_left_click, widget, None)
        return False

    def init_controlpoint(self):
        self.coherence.connect(self.device_found,
                               'Coherence.UPnP.RootDevice.detection_completed')
        self.coherence.connect(self.device_removed,
                               'Coherence.UPnP.RootDevice.removed')
        for device in self.coherence.devices:
            self.device_found(device)

    def call_action(self, widget, action, in_entries, out_entries, status_bar):
        self.debug("in_entries %r", in_entries)
        self.debug("out_entries %r", out_entries)
        context_id = status_bar.get_context_id("Action Statusbar")
        status_bar.pop(context_id)
        status_bar.push(context_id,
                        time.strftime("%H:%M:%S") + " - calling " + action.name)

        kwargs = {}
        for entry, method in in_entries.items():
            if isinstance(method, tuple):
                kwargs[entry] = unicode(method[1]()[method[0]()][0])
            else:
                value = method()
                if type(value) == bool:
                    if value == True:
                        kwargs[entry] = '1'
                    else:
                        kwargs[entry] = '0'
                else:
                    kwargs[entry] = unicode(value)

        def populate(result, entries):
            self.info("result %r", result)
            self.info("entries %r", entries)
            status_bar.pop(context_id)
            status_bar.push(context_id,
                            time.strftime("%H:%M:%S") + " - ok")
            for argument, value in result.items():
                type, method = entries[argument]
                if type == 'boolean':
                    value = means_true(value)
                if type == 'text':
                    method.get_buffer().set_text(value)
                    continue
                method(value)

        def fail(f):
            self.debug(f)
            status_bar.pop(context_id)
            status_bar.push(context_id,
                            time.strftime("%H:%M:%S") + " - fail %s" % f.value)

        self.info("action %s call %r", action.name, kwargs)
        d = action.call(**kwargs)
        d.addCallback(populate, out_entries)
        d.addErrback(fail)

    def device_found(self, device=None, row=None):
        self.info(device.get_friendly_name(),
                  device.get_usn(),
                  device.get_device_type().split(':')[3].lower(),
                  device.get_device_type())
        name = '%s (%s)' % (device.get_friendly_name(), ':'.join(device.get_device_type().split(':')[3:5]))
        item = self.store.append(row, (DEVICE, name, device.get_usn(),
                                       self.icons.get(device.get_device_type().split(':')[3].lower(), self.icons['device']),
                                       device))
        for service in device.services:
            _, _, _, service_class, version = service.service_type.split(':')
            service.subscribe()
            service_item = self.store.append(
                item,
                (SERVICE,
                 ':'.join((service_class, version)),
                 service.service_type, self.service_icon, service))
            variables_item = self.store.append(
                service_item, (-1, 'State Variables', '',
                               self.folder_icon, None))
            for variable in service.get_state_variables(0).values():
                self.store.append(
                    variables_item,
                    (VARIABLE, variable.name, '',
                     self.state_variable_icon, variable))

            for action in sorted(service.get_actions().values(), key=lambda a: a.name):
                action_item = self.store.append(
                    service_item,
                    (ACTION, action.name, '',
                     self.action_icon, action))
                for argument in action.get_in_arguments():
                    self.store.append(
                        action_item,
                        (ARGUMENT, argument.name, '',
                         self.action_arg_in_icon, argument))
                for argument in action.get_out_arguments():
                    self.store.append(
                        action_item, (
                        ARGUMENT, argument.name, '',
                        self.action_arg_out_icon, argument))

        for embedded_device in device.devices:
            self.device_found(embedded_device, row=item)

    def device_removed(self, usn=None):
        self.info('device_removed %r', usn)
        row_count = 0
        for row in self.store:
            if usn == row[UDN_COLUMN]:
                ids = []
                for w in self.windows.keys():
                    if w.startswith(usn):
                        ids.append(w)
                for id in ids:
                    self.windows[id].destroy()
                    del self.windows[id]
                self.store.remove(self.store.get_iter(row_count))
                break
            row_count += 1

    def mediaserver_browse(self, widget, device):
        from mediaserver import MediaServerWidget
        id = '@'.join((device.get_usn(), 'MediaServerBrowse'))
        try:
            self.windows[id].show()
        except:
            ui = MediaServerWidget(self.coherence, device)
            self.windows[id] = ui.window
        #ui.cb_item_right_click = self.button_pressed
        #ui.window.show_all()

    def mediarenderer_control(self, widget, device):
        from mediarenderer import MediaRendererWidget
        id = '@'.join((device.get_usn(), 'MediaRendererControl'))
        try:
            self.windows[id].show()
        except:
            ui = MediaRendererWidget(self.coherence, device)
            self.windows[id] = ui.window

    def igd_control(self, widget, device):
        from igd import IGDWidget
        id = '@'.join((device.get_usn(), 'IGDControl'))
        try:
            self.windows[id].show()
        except:
            ui = IGDWidget(self.coherence, device)
            self.windows[id] = ui.window
