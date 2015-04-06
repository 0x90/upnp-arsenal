#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2009 - Frank Scholz <coherence@beebits.net>

""" Inspector is a UPnP device inspector, or device spy

    Based on the Coherence UPnP/DLNA framework
    http://coherence.beebits.net
"""

import os
import sys

from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor
from twisted.python import usage

from upnp_inspector import __version__
from coherence import __version__ as coherence_version

from upnp_inspector.base import Inspector


class Options(usage.Options):

    optFlags = [['version', 'v', 'print out version']
                ]
    optParameters = [['logfile', 'l', None, 'logfile'],
                    ]

    def __init__(self):
        usage.Options.__init__(self)
        self['options'] = {}

    def opt_version(self):
        print "UPnP-Inspector version:", __version__
        print "using Coherence:", coherence_version
        sys.exit(0)

    def opt_help(self):
        sys.argv.remove('--help')
        print self.__str__()
        sys.exit(0)


if __name__ == '__main__':

    options = Options()
    try:
        options.parseOptions()
    except usage.UsageError, errortext:
        print '%s: %s' % (sys.argv[0], errortext)
        print '%s: Try --help for usage details.' % (sys.argv[0])
        sys.exit(0)

    i = Inspector(logfile=options['logfile'])
    reactor.run()
