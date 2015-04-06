.. -*- mode: rst ; ispell-local-dictionary: "american" -*-

==========================
The UPnP-Inspector
==========================
--------------------------------------------------------------------------
An UPnP Device and Service analyzer based on Coherence
--------------------------------------------------------------------------

:Author:    Frank Scholz
:Copyright: 2008 by Frank Scholz, 2014 by Hartmut Goebel
:Licence:   MIT licence
:Homepage:  http://coherence-project.org/wiki/UPnP-Inspector

The UPnP-Inspector (|Inspector|) is an UPnP Device and Service
analyzer based on `Coherence`__. |Inspector| helps analyzing UPnP
devices and services on your networks. It's both a big help for
debugging and a learning tool. |Inspector| is loosely modeled after
the Intel UPnP Device Spy and the UPnP Test Tool.

__ http://coherence-project.org/

Beside the analyzing functions, |Inspector| can act as a simple `UPnP
ControlPoint`__. You can browse the content of DLNA `MediaServers`__
and control `MediaRenderers`__, e.g. make them play music directly from
the Media Server.

__ http://coherence-project.org/wiki/ControlPoint
__ http://coherence-project.org/wiki/MediaServer
__ http://coherence-project.org/wiki/MediaRenderer

Features
-----------

 * inspect UPnP devices, services, actions and state-variables
 * invoke actions on any service
 * extract UPnP device- and service-description xml-files
 * follow and analyze events
 * interact with well-known devices:

   * browse the ContentDirectory of an UPnP A/V MediaServer and
     inspect its containers and items
   * control an UPnP A/V MediaRenderer

Release 0.2.2 - Let the Sunshine In - includes:

 * a control-window for UPnP A/V MediaRenderers
 * Drag 'n Drop functionality from the MediaServer Browse window to
   the MediaRenderer control
 * a 'Rediscover Devices' menu item
 * a 'Refreshing Container' context menu item and an overall refresh
   upon closing the MediaServer Browse window
 * support for dlna-playcontainer URIs
 * displaying all elements from a DIDLLite fragment


Installing pre-build packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Windows: Please use the setup.exe found at the `project download
   page`_.

:GNU/Linux: Most current GNU/Linux distributions provide packages for
  |Inspector|. Using your Linux distributions software installation tool
  look for a package like `upnp-inspector`. Otherwise you may install
  |Inspector| from source, which is easy on recent GNU/Linux systems.

:Other platforms: Currently we do not know of any prebuild packages
  for other platforms. If you know, please drop us a note.

Requirements and Installation from Source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|Inspector| requires

* `Python 2.x`__ or higher (tested with 2.6, but other
  versions should work, too, Python 3.x is *not* supported),
* `setuptools`_ or `distribute`_ for installation (see below),
* `PyGTK`_, and of course
* Coherence >= 0.6.4 and
* Twisted (which is required by Coherence).

__ http://www.python.org/download/

:Hints for installing on Windows: Following the links above you will
   find .msi and .exe-installers. For PyGTK we suggest using the
   `all-in-one installer <http://www.pygtk.org/downloads.html>`__.
   Simply install this and continue with `installing The Inspector`_.

   You may want to build an installer exe yourself. Please refer to
   the win32 directory of |Inspector|\s source distribution.

:Hints for installing on GNU/Linux: Most current GNU/Linux
   distributions provide packages for the requirements. Look for
   packages names like `python-setuptools` and `python-gtk2` or
   `pygtk2.0`. Simply install them and continue with `installing The
   Inspector`_.

:Hint for installing on other platforms: Many vendors provide Python.
   Please check your vendors software repository. Otherwise please
   download Python 2.6 (or any higher version from the 2.x series) from
   http://www.python.org/download/ and follow the installation
   instructions there.

   After installing Python, install `setuptools`_. You may want to
   read `More Hints on Installing setuptools`_ first.

   Compiling and installing GTK+ and PyGTK for your platform may be
   cumbersome. It may not even be supported. Sorry, we can not help
   here further.


Installing The Inspector
---------------------------------

When you are reading this you most probably already downloaded and
unpacked |Inspector|. Thus installing is as easy as running::

   python ./setup.py install

Otherwise you may install directly using setuptools/easy_install. If
your system has network access installing |Inspector| is a
breeze::

     easy_install upnp-inspector

Without network access download |Inspector| from
http://pypi.python.org/pypi/upnp-inspector and run::

     easy_install upnp-inspector-*.tar.gz


More Hints on Installing setuptools
------------------------------------

|Inspector| uses setuptools for installation. Thus you need
either

  * network access, so the install script will automatically download
    and install setuptools if they are not already installed

or

  * the correct version of setuptools pre-installed using the
    `EasyInstall installation instructions`__. Those instructions also
    have tips for dealing with firewalls as well as how to manually
    download and install setuptools.

__ http://peak.telecommunity.com/DevCenter/EasyInstall#installation-instructions


Custom Installation Locations
------------------------------

|Inspector| is just a single script (aka Python program). So you can
copy it where ever you want (maybe fixing the first line). But it's
easier to just use::

   # install to /usr/local/bin
   python ./setup.py install --prefix /usr/local

   # install to your Home directory (~/bin)
   python ./setup.py install --home ~


Please mind: This effects also the installation of setuptools if they
are not already installed.

For more information about Custom Installation Locations please refer
to the `Custom Installation Locations Instructions`__ before
installing |Inspector|.

__ http://peak.telecommunity.com/DevCenter/EasyInstall#custom-installation-locations>


.. |Inspector| replace:: `The Inspector`

.. _setuptools: http://pypi.python.org/pypi/setuptools
.. _distribute: http://pypi.python.org/pypi/distribute
.. _PyGTK: http://www.pygtk.org/
.. _project download page: https://coherence.beebits.net/download/
