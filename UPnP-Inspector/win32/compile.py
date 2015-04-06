# use the files in this folder first!
#import os, sys
#sys.path.insert(0, os.path.abspath("."))

from bbfreeze import Freezer

includes = ['coherence', 'setuptools', 'cairo',
        'pango', 'gtk', 'pangocairo', 'atk', 'xml',
        'coherence.base',
        #'netifaces'
        ]
f = Freezer("build", includes=includes)
f.addScript("upnp-inspector.py", gui_only=True)
f.include_py = True
f.use_compression = True
f()
