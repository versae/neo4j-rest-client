# -*- coding: utf-8 -*-
try:
    import cPickle as pickle
except:
    import pickle
import unittest
import os

from neo4jrestclient import client


NEO4J_URL = os.environ.get('NEO4J_URL', "http://localhost:7474/db/data/")
NEO4J_VERSION = os.environ.get('NEO4J_VERSION', None)


class GraphDatabaseTesCase(unittest.TestCase):

    def setUp(self):
        self.url = NEO4J_URL
        self.gdb = client.GraphDatabase(self.url)

    def tearDown(self):
        if self.gdb:
            self.gdb.flush()


class PickleTestCase(GraphDatabaseTesCase):

    def test_gdb(self):
        gdb = self.gdb
        p = pickle.dumps(gdb)
        self.assertEqual(gdb, pickle.loads(p))

    def test_node_pickle(self):
        n = self.gdb.nodes.create()
        p = pickle.dumps(n)
        self.assertEqual(n, pickle.loads(p))

    def test_relationship_pickle(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        r = n1.relationships.create("related", n2)
        p = pickle.dumps(r)
        self.assertEqual(r, pickle.loads(p))
