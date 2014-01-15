#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import setup


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

# Dynamically get the constants.
constants = __import__('neo4jrestclient.constants').constants

tests_require = [
    'lockfile>=0.9.1',
    'CacheControl>=0.9.2',
]

setup(
    name='neo4jrestclient',
    version=constants.__version__,
    author=constants.__author__,
    author_email=constants.__email__,
    url=constants.__url__,
    description=constants.__description__,
    long_description=read('README.rst') + "\n\n" + read('CHANGES.txt'),
    license=constants.__license__,
    keywords='neo4j graph graphdb graphdatabase database rest client driver',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
    ],
    zip_safe=False,
    packages=[
        "neo4jrestclient",
    ],
    include_package_data=True,
    install_requires=[
        'requests>=2.1.0',
        'lucene-querybuilder>=0.2',
    ],
    tests_require=tests_require,
    test_suite='neo4jrestclient.tests',
    extras_require={},
)
