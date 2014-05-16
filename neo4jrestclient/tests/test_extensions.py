# -*- coding: utf-8 -*-
import unittest
import os

from neo4jrestclient import constants
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


class ExtensionsTestCase(GraphDatabaseTesCase):

    def test_get_graph_extensions(self):
        fail = False
        try:
            self.gdb.extensions
        except:
            fail = True
        self.assertTrue(not fail)

    def test_get_node_extensions(self):
        fail = False
        n1 = self.gdb.nodes.create()
        try:
            n1.extensions
        except:
            fail = True
        self.assertTrue(not fail)

    @unittest.skipIf(NEO4J_VERSION not in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_gremlin_extension_reference_node(self):
        # Assuming the GremlinPlugin installed
        ext = self.gdb.extensions.GremlinPlugin
        n = self.gdb.nodes.create()
        gremlin_n = ext.execute_script(script='g.v(%s)' % n.id)
        self.assertEqual(gremlin_n, n)

    @unittest.skipIf(NEO4J_VERSION not in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_gremlin_extension_reference_node_returns(self):
        # Assuming the GremlinPlugin installed
        ext = self.gdb.extensions.GremlinPlugin
        n = self.gdb.nodes.create()
        gremlin_n = ext.execute_script(script='g.v(%s)' % n.id,
                                       returns=constants.NODE)
        self.assertEqual(gremlin_n, n)

    @unittest.skipIf(NEO4J_VERSION not in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_gremlin_extension_relationships(self):
        # Assuming the GremlinPlugin installed
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        n3 = self.gdb.nodes.create()
        n1.relationships.create("related", n2)
        n1.relationships.create("related", n3)
        gremlin = self.gdb.extensions.GremlinPlugin.execute_script
        rels = gremlin(script='g.v(%s).outE' % n1.id)
        self.assertEqual(len(rels), 2)
        for rel in rels:
            self.assertTrue(isinstance(rel, client.Relationship))

    @unittest.skipIf(NEO4J_VERSION not in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_gremlin_extension_relationships_returns(self):
        # Assuming the GremlinPlugin installed
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        n3 = self.gdb.nodes.create()
        n1.relationships.create("related", n2)
        n1.relationships.create("related", n3)
        gremlin = self.gdb.extensions.GremlinPlugin.execute_script
        from neo4jrestclient import options as clientDebug
        clientDebug.DEBUG = True
        rels = gremlin(script='g.v(%s).outE' % n1.id,
                       returns=constants.RELATIONSHIP)
        self.assertEqual(len(rels), 2)
        for rel in rels:
            self.assertTrue(isinstance(rel, client.Relationship))
        clientDebug.DEBUG = False

    @unittest.skipIf(NEO4J_VERSION not in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_gremlin_extension_reference_raw_returns(self):
        # Assuming the GremlinPlugin installed
        ext = self.gdb.extensions.GremlinPlugin
        n = self.gdb.nodes.create(name="Test")
        gremlin_n = ext.execute_script(script='g.v(%s)' % n.id,
                                       returns=constants.RAW)
        self.assertEqual(gremlin_n["data"], n.properties)
        self.assertTrue(isinstance(gremlin_n, dict))

    @unittest.skipIf(NEO4J_VERSION not in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_gremlin_results_raw(self):
        # Assuming the GremlinPlugin installed
        ext = self.gdb.extensions.GremlinPlugin
        n = ext.execute_script(script='results = [1,2]', returns=constants.RAW)
        self.assertTrue(isinstance(n, list))
        self.assertEqual(n, [1, 2])
