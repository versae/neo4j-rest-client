# -*- coding: utf-8 -*-
import unittest
import os

from neo4jrestclient import client
from neo4jrestclient import query

NEO4J_URL = os.environ.get('NEO4J_URL', "http://localhost:7474/db/data/")
NEO4J_VERSION = os.environ.get('NEO4J_VERSION', None)


class GraphDatabaseTesCase(unittest.TestCase):

    def setUp(self):
        # A bit of monkey patching to emulate that we are inside IPython
        self.in_ipnb = query.in_ipnb
        query.in_ipnb = lambda: True
        self.url = NEO4J_URL
        self.gdb = client.GraphDatabase(self.url)

    def tearDown(self):
        if self.gdb:
            self.gdb.flush()
        query.in_ipnb = self.in_ipnb


class IPythonTestCase(GraphDatabaseTesCase):

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_ipython_query_raw(self):
        n1 = self.gdb.nodes.create(name="John")
        n2 = self.gdb.nodes.create(name="William")
        n1.knows(n2, since=1982)
        q = """start n=node(*) return n limit 2"""
        result = self.gdb.query(q=q)
        self.assertTrue(len(result._elements_graph) == 2)
        self.assertTrue(len(result._elements_row) == 2)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_ipython_query_returns(self):
        n1 = self.gdb.nodes.create(name="John")
        n2 = self.gdb.nodes.create(name="William")
        n1.knows(n2, since=1982)
        q = """start n=node(*) return n limit 2"""
        result = self.gdb.query(q=q, returns=client.Node)
        self.assertTrue(len(result._elements_graph) == 2)
        self.assertTrue(len(result._elements_row) == 2)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_ipython_query_returns_html(self):
        n1 = self.gdb.nodes.create(name="John")
        n2 = self.gdb.nodes.create(name="William")
        n1.knows(n2, since=1982)
        q = """start n=node(*) return n limit 2"""
        result = self.gdb.query(q=q, returns=client.Node)
        self.assertTrue("div" in result._repr_html_())

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_ipython_query_to_html(self):
        n1 = self.gdb.nodes.create(name="John")
        n2 = self.gdb.nodes.create(name="William")
        n1.knows(n2, since=1982)
        q = """start n=node(*) return n limit 2"""
        result = self.gdb.query(q=q, returns=client.Node)
        self.assertTrue("title" in result.to_html(title="title"))
