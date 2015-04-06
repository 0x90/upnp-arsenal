.. -*- mode: rst ; ispell-local-dictionary: "american" -*-

===========================================
Windows Build for the UPnP-Inspector
===========================================

:Date: 2011-09-19
:Author: lightyear, htgoebel

Setting up dependencies
===========================================

To be able to build the windows installer for the UPnP-Inspector for
Windows you need to have some libraries and runtime environment set
up.

Python
~~~~~~~~~~~~~~~~~~~

First of all you will need Python. Take care that the time this was
written the UPnP-Inspector (or mostly Coherence) did not work with
Python 2.6 or 3k. If this did not change meanwhile, take care to
always download Python in the version 2.5 (2.5.3 at the time beeing).

Following the links below you will find .msi and .exe-installers.
Simply install them.

* `Python 2.x`__ or higher (tested with 2.5 and 2.6, but other
  versions should work, too. Python 3.x is currently *not* supported),
* `setuptools`__ for installation (see below), and

__ http://www.python.org/download/
__ http://pypi.python.org/pypi/setuptools


Setuptools
~~~~~~~~~~~~~~~~~~~

Setuptools is as a strong dependency for coherence and the
UPnP-Inspector as well as a runtime dependency for our development
environment. In any case if you install the python you probably want
to have the handy easy_install command anyway. Install setuptools like
this if you didn't yet:

Download the easy_setup.py from and run python easy_setup.py from the
commandline (maybe you need superuser rights if you aren't a super
user yet).

GTK-Runtime
~~~~~~~~~~~~~~~~~~~

Download and install the `GTK-Runtime`__. Don't you dare to throw away
the downloaded installer! We need it later.

__ http://sourceforge.net/projects/gtk-win/files/

 * `libglade`__ needs to be unpacked into the same directory as the
 GTK dlls.

__ http://ftp.gnome.org/pub/gnome/binaries/win32/libglade/

Python Bindinds for the runtime
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We also need some Python-Bindings for the GTK-Runtime we just
installed. In particular we need:

 * `pygtk`__
 * `pycairo`__
 * `pygobject`__
 
__ http://ftp.gnome.org/pub/gnome/binaries/win32/pygtk/
__ http://ftp.gnome.org/pub/gnome/binaries/win32/pycairo/
__ http://ftp.gnome.org/pub/gnome/binaries/win32/pygobject/



PyWin32
~~~~~~~~~~~~~~~~~~~

And last but not least we need pywin32. Don't ask, just install it,
damn' it! - no seriously, it will be needed to find the right
libraries (like gtk) and run properly.

Build Tools
~~~~~~~~~~~~~~~~~~~

bbfreeze
------------------------

We use the cool bbfreeze project to create our binary of the
Inspector. So we need that as well. It is very simple because we have
easy_install::

   easy_install bbfreeze


internal dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Twisted
-------------------------

http://twistedmatrix.com/trac/wiki/Downloads

If you have Visual-Studio 2003 you can try to install twisted 8.10.0
with easy_install. I was not able to do that so I recommand to do what
I did: download the twisted installer from their website and install
it ;) .

But do it! If you try to install Coherence or UPnP-Inspector before
you did that you might fail.

You'll also have to install some dependencies:
* http://pypi.python.org/pypi/zope.interface
* http://pypi.python.org/pypi/pyOpenSSL

Again this is very simple because we have easy_install::

   easy_install zope.interface pyOpenSSL


Coherence
-------------------------

To be able to build the Inspector you need Coherence of course. You
can simply install it with easy_install::

  easy_install Coherence

This will install Coherence and all its python dependencies (dispite
twisted as we already installed ;) )

The Net thing
-------------------------

We also need one thing that is optional (as it is only needed for
windows)

STILL NOT SURE IF IT IS NEEDED. WORKED W/O ON MY VISTA.

Build
===========================================

So let's get the build system. That is pretty easy with the following
steps:

building the binary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First we need to build the "exe" and corresponding dependencies. that
is done by running::

  python compile.py

in the commandline. This will create a folder called "build". In this
folder you'll find the necessary egg files, bindings for gtk and stuff
and most importantly an upnp-inspector.exe file.

You should be able to run this file directly from the commandline
already. If that doesn't work you don't even have to continue ;) .

package the installer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now we need to package that all together into a nice installer. Take
care that the gtk-runtime installer is in the same folder now. It is
going to be included in the installer and the packaging will fail if
it can't find it.

Simply do a right-click on the win32.nsi file in the explorer. There
should be an entry called "Compile NSIS Script". Click that. Otherwise
you can also just start the NSIS-Tool and load the file into it.

When it is done, you should always press "Test Installer" for a simple
smoketest.

You are done :) . There is now a
"UPNPInspector-VERSION-INSTALLERVERSION-setup.exe" in your folder.
Share it!


Known bugs and todos
===============================

 - add the icon to the binary
 - add the icon to the installer
 - namespace in the installer faulty: UPNPInspector -> UPNP-Inspector
 - fix up the documentation
 - remove the py-debug-binary before releasing
 - uninstaller does not remove start-menu-shortcuts
 - start-menu-shortcut should not contain version in name

plans for after the release
 - talk with the pidgin guys about outsourcing the gtk-installer-part as a NSIS-Plugin because I guess other will need it later as well
 - clean up installer-compile-warnings
 - optional gtk-less-installer
 - outsource coherence to its own installer
