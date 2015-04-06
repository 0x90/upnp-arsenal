# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from upnp_inspector import __version__

packages = find_packages()

long_description = "\n\n".join([
    open("README.txt").read(),
    ])

setup(
    name="UPnP-Inspector",
    version=__version__,
    description="""UPnP Device and Service analyzer""",
    long_description=long_description,
    author="Frank Scholz, Hartmut Goebel",
    author_email='h.goebel@crazy-compilers.com',
    license="MIT",
    packages=packages,
    scripts=['bin/upnp-inspector'],
    url="http://coherence.beebits.net/wiki/UPnP-Inspector",
    download_url='http://coherence.beebits.net/download/UPnP-Inspector-%s.tar.gz' % __version__,
    keywords=['UPnP', 'DLNA'],
    classifiers=['Development Status :: 4 - Beta',
                   'Environment :: X11 Applications :: Gnome',
                   'Environment :: X11 Applications :: GTK',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                ],

    package_data={
        'upnp_inspector': ['icons/*.png'],
    },
    install_requires=[
    'Coherence >= 0.6.4', 'Twisted', 'pygtk', 'setuptools'
    ]
)
