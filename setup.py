#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from distutils.core import setup

__author__ = "Javier de la Rosa"
__credits__ = [
    "Javier de la Rosa",
    "Diego Muñoz Escalante, https://github.com/escalant3",
    "Yashh, https://github.com/yashh",
    "timClicks, https://github.com/timClicks",
    "Mark Henderson, https://github.com/emehrkay",
    "Johan Lundberg, https://github.com/johanlundberg",
    "Mark Ng, https://github.com/markng",
    "kesavkolla, https://github.com/kesavkolla",
    "Andy Denmark, https://github.com/denmark",
]
__license__ = "GPL 3"
__version__ = "1.3.4"
__email__ = "versae@gmail.com"
__url__ = "https://github.com/versae/neo4j-rest-client"
__description__ = """Library to interact with Neo4j standalone REST server"""
__status__ = "Development"

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name='neo4jrestclient',
    version=__version__,
    author=__author__,
    author_email=__email__,
    url=__url__,
    description=__description__,
    long_description=read('README.txt') + "\n\n" + read('CHANGES.txt'),
    license=__license__,
    keywords='neo4j graph graphdb graphdatabase database rest client',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        ],
    zip_safe=False,
    packages=[
        "neo4jrestclient",
    ],
    include_package_data=True,
    install_requires=[
        'httplib2',
    ],
)
