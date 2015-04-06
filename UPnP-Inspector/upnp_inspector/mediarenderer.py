# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>
# Copyright 2014 - Hartmut Goebel <h.goebel@crazy-compilers.com>

import pygtk
pygtk.require("2.0")
import gtk

if __name__ == '__main__':
    from twisted.internet import gtk2reactor
    gtk2reactor.install()
from twisted.internet import reactor
from twisted.internet import task

from coherence import log
from coherence.upnp.core.utils import parse_xml, getPage, means_true

from ._resources import _geticon


class MediaRendererWidget(log.Loggable):
    logCategory = 'inspector'

    def __init__(self, coherence, device):
        self.coherence = coherence
        self.device = device
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.hide)
        self.window.set_default_size(480, 200)
        try:
            title = 'MediaRenderer %s' % device.get_friendly_name()
        except:
            title = 'MediaRenderer'
        self.window.set_title(title)

        self.window.drag_dest_set(
            gtk.DEST_DEFAULT_DROP, [('upnp/metadata', 0, 1)],
            gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_PRIVATE)
        self.window.connect('drag_motion', self.motion_cb)
        self.window.connect('drag_drop', self.drop_cb)
        self.window.connect("drag_data_received", self.received_cb)

        vbox = gtk.VBox(homogeneous=False, spacing=10)

        hbox = gtk.HBox(homogeneous=False, spacing=10)
        hbox.set_border_width(2)
        self.album_art_image = gtk.Image()
        self.blank_icon = _geticon('blankalbum.png')
        self.album_art_image.set_from_pixbuf(self.blank_icon)
        hbox.pack_start(self.album_art_image, False, False, 2)
        #icon_loader = gtk.gdk.PixbufLoader()
        #icon_loader.write(urllib.urlopen(str(res.data)).read())
        #icon_loader.close()

        vbox.pack_start(hbox, False, False, 2)
        textbox = gtk.VBox(homogeneous=False, spacing=10)
        self.title_text = gtk.Label("<b>title</b>")
        self.title_text.set_use_markup(True)
        textbox.pack_start(self.title_text, False, False, 2)
        self.album_text = gtk.Label("album")
        self.album_text.set_use_markup(True)
        textbox.pack_start(self.album_text, False, False, 2)
        self.artist_text = gtk.Label("artist")
        self.artist_text.set_use_markup(True)
        textbox.pack_start(self.artist_text, False, False, 2)
        hbox.pack_start(textbox, False, False, 2)

        seekbox = gtk.HBox(homogeneous=False, spacing=10)
        self.position_min_text = gtk.Label("0:00")
        self.position_min_text.set_use_markup(True)
        seekbox.pack_start(self.position_min_text, False, False, 2)
        adjustment = gtk.Adjustment(value=0, lower=0, upper=240,
                                    step_incr=1, page_incr=20)  #, page_size=20)
        self.position_scale = gtk.HScale(adjustment=adjustment)
        self.position_scale.set_draw_value(True)
        self.position_scale.set_value_pos(gtk.POS_BOTTOM)
        self.position_scale.set_sensitive(False)
        self.position_scale.connect("format-value", self.format_position)
        self.position_scale.connect('change-value', self.position_changed)
        seekbox.pack_start(self.position_scale, True, True, 2)
        self.position_max_text = gtk.Label("0:00")
        self.position_max_text.set_use_markup(True)
        seekbox.pack_end(self.position_max_text, False, False, 2)
        vbox.pack_start(seekbox, False, False, 2)

        buttonbox = gtk.HBox(homogeneous=False, spacing=10)
        self.prev_button = self.make_button('media-skip-backward.png',
                                            self.skip_backward, sensitive=False)
        buttonbox.pack_start(self.prev_button, False, False, 2)
        self.seek_backward_button = self.make_button(
            'media-seek-backward.png',
            callback=self.seek_backward, sensitive=False)
        buttonbox.pack_start(self.seek_backward_button, False, False, 2)
        self.stop_button = self.make_button(
            'media-playback-stop.png', callback=self.stop, sensitive=False)
        buttonbox.pack_start(self.stop_button, False, False, 2)
        self.start_button = self.make_button(
            'media-playback-start.png',
            callback=self.play_or_pause, sensitive=False)
        buttonbox.pack_start(self.start_button, False, False, 2)
        self.seek_forward_button = self.make_button(
            'media-seek-forward.png',
            callback=self.seek_forward, sensitive=False)
        buttonbox.pack_start(self.seek_forward_button, False, False, 2)
        self.next_button = self.make_button(
            'media-skip-forward.png', self.skip_forward, sensitive=False)
        buttonbox.pack_start(self.next_button, False, False, 2)

        hbox = gtk.HBox(homogeneous=False, spacing=10)
        #hbox.set_size_request(240,-1)
        adjustment = gtk.Adjustment(value=0, lower=0, upper=100,
                                    step_incr=1, page_incr=20)  #, page_size=20)
        self.volume_scale = gtk.HScale(adjustment=adjustment)
        self.volume_scale.set_size_request(140, -1)
        self.volume_scale.set_draw_value(False)
        self.volume_scale.connect('change-value', self.volume_changed)
        hbox.pack_start(self.volume_scale, False, False, 2)
        button = gtk.Button()
        self.volume_image = gtk.Image()
        self.volume_low_icon = _geticon('audio-volume-low.png')
        self.volume_image.set_from_pixbuf(self.volume_low_icon)
        button.set_image(self.volume_image)
        button.connect("clicked", self.mute)

        self.volume_medium_icon = _geticon('audio-volume-medium.png')
        self.volume_high_icon = _geticon('audio-volume-high.png')
        self.volume_muted_icon = _geticon('audio-volume-muted.png')
        hbox.pack_end(button, False, False, 2)

        buttonbox.pack_end(hbox, False, False, 2)
        vbox.pack_start(buttonbox, False, False, 2)

        self.pause_button_image = gtk.Image()
        icon = _geticon('media-playback-pause.png')
        self.pause_button_image.set_from_pixbuf(icon)
        self.start_button_image = self.start_button.get_image()

        self.status_bar = gtk.Statusbar()
        context_id = self.status_bar.get_context_id("Statusbar")
        vbox.pack_end(self.status_bar, False, False, 2)

        self.window.add(vbox)
        self.window.show_all()

        self.seeking = False

        self.position_loop = task.LoopingCall(self.get_position)

        service = self.device.get_service_by_type('RenderingControl')
        #volume_variable = service.get_state_variable('Volume')
        #print "volume_variable",volume_variable.value
        #try:
        #    volume = int(volume_variable.value)
        #    if int(scale.get_value()) != volume:
        #        self.volume_scale.set_value(volume)
        #except:
        #    pass
        for name, callback in (
            ('Volume', self.state_variable_change),
            ('Mute', self.state_variable_change),
            ):
            service.subscribe_for_variable(name, callback=callback)

        service = self.device.get_service_by_type('AVTransport')
        if service is not None:
            for name, callback in (
                ('AVTransportURI', self.state_variable_change),
                ('CurrentTrackMetaData', self.state_variable_change),
                ('TransportState', self.state_variable_change),
                ('CurrentTransportActions', self.state_variable_change),
                ('AbsTime', self.state_variable_change),
                ('TrackDuration', self.state_variable_change),
                ):
                service.subscribe_for_variable(name, callback=callback)

        self.get_position()

    def motion_cb(self, wid, context, x, y, time):
        #print 'drag_motion'
        context.drag_status(gtk.gdk.ACTION_COPY, time)
        return True

    def drop_cb(self, wid, context, x, y, time):
        #print('\n'.join([str(t) for t in context.targets]))
        context.finish(True, False, time)
        return True

    def received_cb(self, widget, context, x, y, selection, targetType,
                            time):
        #print "received_cb", targetType
        if targetType == 1:
            metadata = selection.data
            #print "got metadata", metadata
            from coherence.upnp.core import DIDLLite
            elt = DIDLLite.DIDLElement.fromString(metadata)
            if elt.numItems() == 1:
                service = self.device.get_service_by_type('ConnectionManager')
                if service != None:
                    local_protocol_infos = service.get_state_variable(
                        'SinkProtocolInfo').value.split(',')
                    #print local_protocol_infos
                    item = elt.getItems()[0]
                    try:
                        res = item.res.get_matching(local_protocol_infos,
                                                    protocol_type='internal')
                        if len(res) == 0:
                            res = item.res.get_matching(local_protocol_infos)
                        if len(res) > 0:
                            res = res[0]
                            remote_protocol, remote_network, remote_content_format, _ = res.protocolInfo.split(':')
                            d = self.stop()
                            d.addCallback(lambda x: self.set_uri(res.data, metadata))
                            d.addCallback(lambda x: self.play_or_pause(force_play=True))
                            d.addErrback(self.handle_error)
                            d.addErrback(self.handle_error)
                    except AttributeError:
                        print "Sorry, we currently support only single items!"
                else:
                    print "can't check for the best resource!"

    def make_button(self, icon, callback=None, sensitive=True):
        icon = _geticon(icon)
        button = gtk.Button()
        image = gtk.Image()
        image.set_from_pixbuf(icon)
        button.set_image(image)
        button.connect("clicked", lambda x: callback())
        button.set_sensitive(sensitive)
        return button

    def hide(self, w, e):
        w.hide()
        return True

    def state_variable_change(self, variable):
        print "%s %r" % (variable.name, variable.value)
        if variable.name == 'CurrentTrackMetaData':
            if variable.value != None and len(variable.value) > 0:
                try:
                    from coherence.upnp.core import DIDLLite
                    elt = DIDLLite.DIDLElement.fromString(variable.value)
                    for item in elt.getItems():
                        print "now playing:", repr(item.artist),
                        print "-", repr(item.title),
                        print "(%s/%r)" % (item.id, item.upnp_class)
                        self.title_text.set_markup("<b>%s</b>" % item.title)
                        if item.album != None:
                            self.album_text.set_markup(item.album)
                        else:
                            self.album_text.set_markup('')
                        if item.artist != None:
                            self.artist_text.set_markup("<i>%s</i>" %
                                                        item.artist)
                        else:
                            self.artist_text.set_markup("")

                        def got_icon(icon):
                            icon = icon[0]
                            icon_loader = gtk.gdk.PixbufLoader()
                            icon_loader.write(icon)
                            icon_loader.close()
                            icon = icon_loader.get_pixbuf()
                            icon = icon.scale_simple(128, 128,
                                                     gtk.gdk.INTERP_BILINEAR)
                            self.album_art_image.set_from_pixbuf(icon)

                        if item.upnp_class.startswith('object.item.audioItem') and item.albumArtURI != None:
                            d = getPage(item.albumArtURI)
                            d.addCallback(got_icon)
                        elif item.upnp_class.startswith('object.item.imageItem'):
                            res = item.res.get_matching('http-get:*:image/:*')
                            if len(res) > 0:
                                res = res[0]
                                d = getPage(res.data)
                                d.addCallback(got_icon)
                            else:
                                self.album_art_image.set_from_pixbuf(self.blank_icon)
                        else:
                            self.album_art_image.set_from_pixbuf(self.blank_icon)


                except SyntaxError:
                    #print "seems we haven't got an XML string"
                    return
            else:
                self.title_text.set_markup('')
                self.album_text.set_markup('')
                self.artist_text.set_markup('')
                self.album_art_image.set_from_pixbuf(self.blank_icon)

        elif variable.name == 'TransportState':
            print variable.name, 'changed from', variable.old_value,
            print 'to', variable.value
            if variable.value == 'PLAYING':
                service = self.device.get_service_by_type('AVTransport')
                if 'Pause' in service.get_actions():
                    self.start_button.set_image(self.pause_button_image)
                try:
                    self.position_loop.start(1.0, now=True)
                except:
                    pass
            elif variable.value != 'TRANSITIONING':
                self.start_button.set_image(self.start_button_image)
                try:
                    self.position_loop.stop()
                except:
                    pass
            if variable.value == 'STOPPED':
                self.get_position()

            context_id = self.status_bar.get_context_id("Statusbar")
            self.status_bar.pop(context_id)
            self.status_bar.push(context_id, "%s" % variable.value)

        elif variable.name == 'CurrentTransportActions':
            try:
                actions = map(lambda x: x.upper(), variable.value.split(','))
                if 'SEEK' in actions:
                    self.position_scale.set_sensitive(True)
                    self.seek_forward_button.set_sensitive(True)
                    self.seek_backward_button.set_sensitive(True)
                else:
                    self.position_scale.set_sensitive(False)
                    self.seek_forward_button.set_sensitive(False)
                    self.seek_backward_button.set_sensitive(False)
                self.start_button.set_sensitive('PLAY' in actions)
                self.stop_button.set_sensitive('STOP' in actions)
                self.prev_button.set_sensitive('PREVIOUS' in actions)
                self.next_button.set_sensitive('NEXT' in actions)
            except:
                #very unlikely to happen
                import traceback
                print traceback.format_exc()

        elif variable.name == 'AVTransportURI':
            print variable.name, 'changed from', variable.old_value,
            print 'to', variable.value
            if variable.value != '':
                pass
                #self.seek_backward_button.set_sensitive(True)
                #self.stop_button.set_sensitive(True)
                #self.start_button.set_sensitive(True)
                #self.seek_forward_button.set_sensitive(True)
            else:
                #self.seek_backward_button.set_sensitive(False)
                #self.stop_button.set_sensitive(False)
                #self.start_button.set_sensitive(False)
                #self.seek_forward_button.set_sensitive(False)
                self.album_art_image.set_from_pixbuf(self.blank_icon)
                self.title_text.set_markup('')
                self.album_text.set_markup('')
                self.artist_text.set_markup('')

        elif variable.name == 'Volume':
            try:
                volume = int(variable.value)
                print "volume value", volume
                if int(self.volume_scale.get_value()) != volume:
                    self.volume_scale.set_value(volume)
                service = self.device.get_service_by_type('RenderingControl')
                mute_variable = service.get_state_variable('Mute')
                if means_true(mute_variable.value) == True:
                    self.volume_image.set_from_pixbuf(self.volume_muted_icon)
                elif volume < 34:
                    self.volume_image.set_from_pixbuf(self.volume_low_icon)
                elif volume < 67:
                    self.volume_image.set_from_pixbuf(self.volume_medium_icon)
                else:
                    self.volume_image.set_from_pixbuf(self.volume_high_icon)

            except:
                import traceback
                print traceback.format_exc()
                pass

        elif variable.name == 'Mute':
            service = self.device.get_service_by_type('RenderingControl')
            volume_variable = service.get_state_variable('Volume')
            volume = volume_variable.value
            if means_true(variable.value) == True:
                self.volume_image.set_from_pixbuf(self.volume_muted_icon)
            elif volume < 34:
                self.volume_image.set_from_pixbuf(self.volume_low_icon)
            elif volume < 67:
                self.volume_image.set_from_pixbuf(self.volume_medium_icon)
            else:
                self.volume_image.set_from_pixbuf(self.volume_high_icon)

    def seek_backward(self):
        self.seeking = True
        value = self.position_scale.get_value()
        value = int(value)
        seconds = max(0, value - 20)

        hours = seconds / 3600
        seconds = seconds - hours * 3600
        minutes = seconds / 60
        seconds = seconds - minutes * 60
        target = "%d:%02d:%02d" % (hours, minutes, seconds)

        def handle_result(r):
            self.seeking = False
            #self.get_position()

        service = self.device.get_service_by_type('AVTransport')
        seek_modes = service.get_state_variable('A_ARG_TYPE_SeekMode').allowed_values
        unit = 'ABS_TIME'
        if 'ABS_TIME' not in seek_modes:
            if 'REL_TIME' in seek_modes:
                unit = 'REL_TIME'
                target = "-%d:%02d:%02d" % (0, 0, 20)
                print "rel-seek", unit, target

        action = service.get_action('Seek')
        d = action.call(InstanceID=0, Unit=unit, Target=target)
        d.addCallback(handle_result)
        d.addErrback(self.handle_error)
        return d

    def seek_forward(self):
        self.seeking = True
        value = self.position_scale.get_value()
        value = int(value)
        max = int(self.position_scale.get_adjustment().upper)
        seconds = min(max, value + 20)

        hours = seconds / 3600
        seconds = seconds - hours * 3600
        minutes = seconds / 60
        seconds = seconds - minutes * 60
        target = "%d:%02d:%02d" % (hours, minutes, seconds)

        def handle_result(r):
            self.seeking = False
            #self.get_position()

        service = self.device.get_service_by_type('AVTransport')
        seek_modes = service.get_state_variable('A_ARG_TYPE_SeekMode').allowed_values
        unit = 'ABS_TIME'
        if 'ABS_TIME' not in seek_modes:
            if 'REL_TIME' in seek_modes:
                unit = 'REL_TIME'
                target = "+%d:%02d:%02d" % (0, 0, 20)
                print "rel-seek", unit, target

        action = service.get_action('Seek')
        d = action.call(InstanceID=0, Unit=unit, Target=target)
        d.addCallback(handle_result)
        d.addErrback(self.handle_error)
        return d

    def play_or_pause(self, force_play=False):
        print "play_or_pause"
        service = self.device.get_service_by_type('AVTransport')
        variable = service.get_state_variable('TransportState', instance=0)
        print variable.value
        if force_play == True or variable.value != 'PLAYING':
            action = service.get_action('Play')
            d = action.call(InstanceID=0, Speed=1)
        else:
            action = service.get_action('Pause')
            d = action.call(InstanceID=0)
        d.addCallback(self.handle_result)
        d.addErrback(self.handle_error)
        return d

    def __AVTransport_action(self, action):
        service = self.device.get_service_by_type('AVTransport')
        action = service.get_action('Stop')
        d = action.call(InstanceID=0)
        d.addCallback(self.handle_result)
        d.addErrback(self.handle_error)
        return d

    def stop(self):
        print "stop"
        return self.__AVTransport_action('Stop')

    def skip_backward(self):
        return self.__AVTransport_action('Previous')

    def skip_forward(self):
        return self.__AVTransport_action('Next')

    def set_uri(self, url, didl):
        print "set_uri %s %r" % (url, didl)
        service = self.device.get_service_by_type('AVTransport')
        action = service.get_action('SetAVTransportURI')
        d = action.call(InstanceID=0, CurrentURI=url,
                                     CurrentURIMetaData=didl)
        d.addCallback(self.handle_result)
        d.addErrback(self.handle_error)
        return d

    def position_changed(self, range, scroll, value):

        old_value = self.position_scale.get_value()
        #print "position_changed", old_value, value
        new_value = value - old_value
        #print "position_changed to ", new_value
        if new_value < 0 and new_value > -1.0:
            return
        if new_value >= 0 and new_value < 1.0:
            return

        self.seeking = True
        adjustment = range.get_adjustment()
        value = int(value)
        max = int(adjustment.upper)
        seconds = target_seconds = min(max, value)

        hours = seconds / 3600
        seconds = seconds - hours * 3600
        minutes = seconds / 60
        seconds = seconds - minutes * 60
        target = "%d:%02d:%02d" % (hours, minutes, seconds)

        service = self.device.get_service_by_type('AVTransport')

        seek_modes = service.get_state_variable('A_ARG_TYPE_SeekMode').allowed_values
        unit = 'ABS_TIME'
        if 'ABS_TIME' not in seek_modes:
            if 'REL_TIME' in seek_modes:
                unit = 'REL_TIME'
                seconds = int(new_value)

                sign = '+'
                if seconds < 0:
                    sign = '-'
                    seconds = seconds * -1

                hours = seconds / 3600
                seconds = seconds - hours * 3600
                minutes = seconds / 60
                seconds = seconds - minutes * 60
                target = "%s%d:%02d:%02d" % (sign, hours, minutes, seconds)
                print "rel-seek", unit, target

        def handle_result(r):
            self.seeking = False
            #self.get_position()

        action = service.get_action('Seek')
        d = action.call(InstanceID=0, Unit=unit, Target=target)
        d.addCallback(handle_result)
        d.addErrback(self.handle_error)

    def format_position(self, scale, value):
        seconds = int(value)
        hours = seconds / 3600
        seconds = seconds - hours * 3600
        minutes = seconds / 60
        seconds = seconds - minutes * 60
        if hours > 0:
            return "%d:%02d:%02d" % (hours, minutes, seconds)
        else:
            return "%d:%02d" % (minutes, seconds)

    def get_position(self):

        if self.seeking == True:
            return

        def handle_result(r, service):
            try:
                duration = r['TrackDuration']
                h, m, s = [int(x) for x in duration.split(':')]
                if int(h) > 0:
                    duration = '%d:%02d:%02d' % (h, m, s)
                else:
                    duration = '%d:%02d' % (m, s)
                seconds = (h * 3600) + (m * 60) + s
                self.position_scale.set_range(0, max(0.1, seconds))
                self.position_max_text.set_markup(duration)
                actions = service.get_state_variable('CurrentTransportActions')
                try:
                    actions = actions.value.split(',')
                    if 'SEEK' in actions:
                        self.position_scale.set_sensitive(True)
                except AttributeError:
                    pass
            except:
                #import traceback
                #print traceback.format_exc()
                try:
                    self.position_scale.set_range(0, 0)
                except:
                    pass
                self.position_max_text.set_markup('0:00')
                self.position_scale.set_sensitive(False)
                pass

            try:
                if self.seeking == False:
                    position = r['AbsTime']
                    h, m, s = position.split(':')
                    position = (int(h) * 3600) + (int(m) * 60) + int(s)
                    self.position_scale.set_value(position)
            except:
                #import traceback
                #print traceback.format_exc()
                pass

        service = self.device.get_service_by_type('AVTransport')
        try:
            action = service.get_action('GetPositionInfo')
            d = action.call(InstanceID=0)
            d.addCallback(handle_result, service)
            d.addErrback(self.handle_error)
            return d
        except AttributeError:
            # the device and its services are gone
            pass

    def volume_changed(self, range, scroll, value):
        value = int(value)
        if value > 100:
            value = 100
        print "volume changed", value
        service = self.device.get_service_by_type('RenderingControl')
        action = service.get_action('SetVolume')
        d = action.call(InstanceID=0,
                    Channel='Master',
                    DesiredVolume=value)
        d.addCallback(self.handle_result)
        d.addErrback(self.handle_error)
        return d

    def mute(self, w):
        service = self.device.get_service_by_type('RenderingControl')
        action = service.get_action('SetMute')
        mute_variable = service.get_state_variable('Mute')
        if means_true(mute_variable.value) == False:
            new_mute = '1'
        else:
            new_mute = '0'
        print "Mute new:", new_mute
        d = action.call(InstanceID=0,
                        Channel='Master',
                        DesiredMute=new_mute)
        d.addCallback(self.handle_result)
        d.addErrback(self.handle_error)
        return d

    def handle_error(self, e):
        print 'we have an error', e
        return e

    def handle_result(self, r):
        print "done", r
        return r

if __name__ == '__main__':

    MediaRendererWidget.hide = lambda x, y, z: reactor.stop()
    i = MediaRendererWidget(None, None)
    reactor.run()
