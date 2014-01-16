# -*- coding: utf-8 -*-
import unittest
import os

from neo4jrestclient import client
from neo4jrestclient.exceptions import NotFoundError


NEO4J_URL = os.environ.get('NEO4J_URL', "http://localhost:7474/db/data/")
NEO4J_VERSION = os.environ.get('NEO4J_VERSION', None)


class GraphDatabaseTesCase(unittest.TestCase):

    def setUp(self):
        self.url = NEO4J_URL
        self.gdb = client.GraphDatabase(self.url)

    def tearDown(self):
        if self.gdb:
            self.gdb.flush()


class RelationshipsTestCase(GraphDatabaseTesCase):

    def test_create_relationship(self):
        n1 = self.gdb.node()
        n2 = self.gdb.node()
        rel = n1.Knows(n2)
        self.assertEqual(rel.properties, {})

    def test_create_relationship_functional(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        rel = n1.relationships.create("Knows", n2)
        self.assertEqual(rel.properties, {})

    def test_create_relationship_functional_safe(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        r1 = n1.relationships.create("recommends ñapa motörhead", n2)
        self.assertEqual(r1.properties, {})
        self.assertEqual(r1.type, "recommends ñapa motörhead")
        r2 = self.gdb.relationships.get(r1.id)
        self.assertEqual(r1.type, r2.type)

    def test_create_relationship_properties(self):
        n1 = self.gdb.node()
        n2 = self.gdb.node()
        rel = n1.Knows(n2, since=1970)
        self.assertEqual(rel.properties, {"since": 1970})

    def test_set_relationships_properties_numbers_set(self):
        n1 = self.gdb.node()
        n2 = self.gdb.node()
        rel = n1.Knows(n2)
        properties = {"name": "Jimmy Doe", "age": 30, "active": False}
        rel.properties = properties
        self.assertEqual(rel.properties, properties)

    def test_create_relationship_functional_properties(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        rel = n1.relationships.create("Knows", n2, since=1970)
        self.assertEqual(rel.properties, {"since": 1970})

    def test_set_relationship_property_safe(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        rel = n1.relationships.create("Knows", n2,
                                      language="Español antigüillo")
        rel.set("Idioma de los subtítulos", "Español antigüillo")
        self.assertEqual(rel.get("Idioma de los subtítulos"),
                         rel.get("language"))

    def test_set_relationship_properties_safe(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        r1 = n1.relationships.create("Knows", n2)
        r1.properties = {"Idioma de los subtítulos": "Español antigüillo"}
        r1_properties = r1.properties
        r2 = self.gdb.relationships.get(r1.id)
        r2_properties = r2.properties
        self.assertEqual(r1_properties, r2_properties)

    def test_delete_relationship(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        rel = n1.relationships.create("Knows", n2, since=1970)
        rel.delete()
        self.assertEqual(len(n1.relationships.outgoing("Knows")), 0)

    def test_get_relationship(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        rel = n1.relationships.create("Knows", n2, since=1970)
        self.assertTrue(isinstance(rel, client.Relationship))

    def test_delete_relationship_not_found(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        rel = n1.relationships.create("Knows", n2, since=1970)
        rel_id = rel.id
        rel.delete()
        self.assertRaises(NotFoundError, self.gdb.relationships.get,
                          rel_id)
