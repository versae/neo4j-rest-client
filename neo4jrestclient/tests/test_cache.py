# -*- coding: utf-8 -*-
try:
    from imp import reload
except ImportError:
    reload
import unittest
import os

from neo4jrestclient import client
from neo4jrestclient import options
from neo4jrestclient import request


NEO4J_URL = os.environ.get('NEO4J_URL', "http://localhost:7474/db/data/")
NEO4J_VERSION = os.environ.get('NEO4J_VERSION', None)


class GraphDatabaseTesCase(unittest.TestCase):

    def setUp(self):
        self.url = NEO4J_URL
        self.gdb = client.GraphDatabase(self.url)

    def tearDown(self):
        from neo4jrestclient import options as clientCacheDebug
        clientCacheDebug.DEBUG = False
        clientCacheDebug.CACHE = False
        if self.gdb:
            self.gdb.flush()


class FakeCache(object):
    def __init__(self, called):
        self.called = called
        self.dict = {}

    def get(self, key):
        self.called['get'] = True
        return self.dict.get(key, None)

    def set(self, key, value):
        self.called['set'] = True
        self.dict[key] = value

    def delete(self, key):
        if key in self.dict:
            del self.dict[key]


class XtraCacheTestCase(unittest.TestCase):

    def setUp(self):
        self.cache_called = {}
        self.cache = options.CACHE
        self.cache_store = options.CACHE
        options.CACHE = True
        options.CACHE_STORE = FakeCache(self.cache_called)
        # reload modules now cache set
        reload(request)
        reload(client)
        self.gdb = client.GraphDatabase(NEO4J_URL)

    def test_custom_cache_used(self):
        n = self.gdb.nodes.create()
        response = request.session.get(n.url)
        self.assertTrue(hasattr(response, "from_cache"))

    def tearDown(self):
        # leave everything as we found it
        options.CACHE = self.cache
        options.CACHE_STORE = self.cache_store
        reload(request)
        reload(client)
        client
