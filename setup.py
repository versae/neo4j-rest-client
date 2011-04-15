#!/usr/bin/env python
import os

from distutils.core import setup

from neo4jrestclient import constants


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name='neo4jrestclient',
    version=constants.__version__,
    author=constants.__author__,
    author_email=constants.__email__,
    url=constants.__url__,
    description=constants.__description__,
    long_description=read('README.rst'),
    license=constants.__license__,
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
