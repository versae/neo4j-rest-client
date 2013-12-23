# -*- coding: utf-8 -*-
from datetime import datetime
import unittest
import os

from neo4jrestclient import client
from neo4jrestclient.utils import text_type


NEO4J_URL = os.environ.get('NEO4J_URL', "http://localhost:7474/db/data/")
NEO4J_VERSION = os.environ.get('NEO4J_VERSION', None)


class GraphDatabaseTesCase(unittest.TestCase):

    def setUp(self):
        self.url = NEO4J_URL
        self.gdb = client.GraphDatabase(self.url)

    def tearDown(self):
        if self.gdb:
            self.gdb.flush()


class QueryTestCase(GraphDatabaseTesCase):

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_query_raw(self):
        n1 = self.gdb.nodes.create(name="John")
        n2 = self.gdb.nodes.create(name="William")
        n1.knows(n2, since=1982)
        q = """start n=node(*) return n"""
        result = self.gdb.query(q=q)
        self.assertTrue(result is not None)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_query_raw_returns(self):
        n1 = self.gdb.nodes.create(name="John")
        n2 = self.gdb.nodes.create(name="William")
        n1.knows(n2, since=1982)
        q = """start n=node(*) return n limit 2"""
        results = self.gdb.query(q=q, returns=[client.Node])
        row1, row2 = results
        m1, m2 = row1[0], row2[0]
        self.assertTrue(isinstance(m1, client.Node))
        self.assertTrue(isinstance(m2, client.Node))

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_query_raw_returns_tuple(self):
        n1 = self.gdb.nodes.create(name="John")
        n2 = self.gdb.nodes.create(name="William")
        rel_type = u"rel%s" % text_type(datetime.now().strftime('%s%f'))
        r = n1.relationships.create(rel_type, n2, since=1982)
        q = """start n=node(*) match n-[r:%s]-() """ \
            """return n, n.name, r, r.since""" % rel_type
        results = self.gdb.query(q, returns=(client.Node, text_type,
                                             client.Relationship))
        for node, name, rel, date in results:
            self.assertTrue(node in (n1, n2))
            self.assertTrue(name in (u"John", u"William"))
            self.assertEqual(rel, r)
            self.assertEqual(date, 1982)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_query_params_returns_tuple(self):
        n1 = self.gdb.nodes.create(name="John")
        n2 = self.gdb.nodes.create(name="William")
        rel_type = u"rel%s" % text_type(datetime.now().strftime('%s%f'))
        r = n1.relationships.create(rel_type, n2, since=1982)
        q = """start n=node(*) match n-[r:`{rel}`]-() """ \
            """return n, n.name, r, r.since"""
        params = {
            "rel": rel_type,
        }
        results = self.gdb.query(q, params=params,
                                 returns=(client.Node, text_type,
                                          client.Relationship))
        for node, name, rel, date in results:
            self.assertTrue(node in (n1, n2))
            self.assertTrue(name in (u"John", u"William"))
            self.assertEqual(rel, r)
            self.assertEqual(date, 1982)
