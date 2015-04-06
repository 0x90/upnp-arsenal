# -*- coding: utf-8 -*-
#
# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php
#
# Copyright 2014 - Hartmut Goebel <h.goebel@crazy-compilers.com>

import os
from pkg_resources import resource_filename

import gtk

def _geticon_path(name):
    return resource_filename(__name__, os.path.join('icons', name))

def _geticon(name):
    """Return a pixbuf for the icon named param:`name`."""
    filename = resource_filename(__name__, os.path.join('icons', name))
    return gtk.gdk.pixbuf_new_from_file(filename)
