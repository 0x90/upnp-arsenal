# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>
# Copyright 2014 - Hartmut Goebel <h.goebel@crazy-compilers.com>

import pygtk
pygtk.require("2.0")
import gtk

from upnp_inspector import __version__
from ._resources import _geticon

class AboutWidget():

    def __init__(self):
        self.window = gtk.AboutDialog()
        try:
            # set_program_name is new in PyGTK 2.12
            self.window.set_program_name('UPnP Inspector')
        except AttributteError:
            # set_name is deprecated in PyGTK 2.12
            self.window.set_name('UPnP Inspector')
        self.window.set_version(__version__)
        self.window.set_copyright('(c) Frank Scholz <coherence@beebits.net>\n'
                                  '(c) Hartmut Goebel <h.goebel@crazy-compilers.com>')
        self.window.set_comments(
            "An UPnP Device and Service analyzer,\n"
            "based on the Coherence DLNA/UPnP framework.\n"
            "Modeled after the Intel UPnP Device Spy.")
        self.window.set_license(
            "MIT\n\nIcons:\n"
            "Tango Project: Creative Commons Attribution Share-Alike\n"
            "David Göthberg: Public Domain")
        self.window.set_website('http://coherence.beebits.net')
        self.window.set_authors([
            'Frank Scholz <fs@beebits.net>',
            'Michael Weinrich <testsuite@michael-weinrich.de>',
            'Hartmut Goebel <h.goebel@crazy-compilers.com>'])
        self.window.set_artists([
            'Tango Desktop Project http://tango.freedesktop.org',
            'David Göthberg: http://commons.wikimedia.org/wiki/User:Davidgothberg',
            'Karl Vollmer: http://ampache.org'])

        logo = _geticon('inspector-logo.png')
        self.window.set_logo(logo)

        self.window.show_all()

        self.window.connect('response', self.response)

    def response(self, widget, response):
        widget.destroy()
        return True
