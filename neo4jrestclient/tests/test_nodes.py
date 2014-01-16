# -*- coding: utf-8 -*-
from datetime import datetime
import unittest
import os

from neo4jrestclient import client
from neo4jrestclient.exceptions import NotFoundError, StatusException

NEO4J_URL = os.environ.get('NEO4J_URL', "http://localhost:7474/db/data/")
NEO4J_VERSION = os.environ.get('NEO4J_VERSION', None)


class GraphDatabaseTesCase(unittest.TestCase):

    def setUp(self):
        self.url = NEO4J_URL
        self.gdb = client.GraphDatabase(self.url)

    def tearDown(self):
        if self.gdb:
            self.gdb.flush()


class NodesTestCase(GraphDatabaseTesCase):

    def test_connection_cache(self):
        from neo4jrestclient import options as clientCache
        clientCache.CACHE = True
        gdb = client.GraphDatabase(self.url)
        clientCache.CACHE = False
        self.assertEqual(gdb.url, self.url)

    def test_connection_debug(self):
        from neo4jrestclient import options as clientDebug
        clientDebug.DEBUG = True
        gdb = client.GraphDatabase(self.url)
        clientDebug.DEBUG = False
        self.assertEqual(gdb.url, self.url)

    def test_connection_cache_debug(self):
        from neo4jrestclient import options as clientCacheDebug
        clientCacheDebug.CACHE = True
        clientCacheDebug.DEBUG = True
        gdb = client.GraphDatabase(self.url)
        clientCacheDebug.CACHE = False
        clientCacheDebug.DEBUG = False
        self.assertEqual(gdb.url, self.url)

    def test_create_node(self):
        n = self.gdb.nodes.create()
        self.assertEqual(n.properties, {})

    def test_create_node_properties(self):
        n = self.gdb.nodes.create(name="John Doe", profession="Hacker")
        self.assertEqual(n.properties, {"name": "John Doe",
                                        "profession": "Hacker"})

    def test_create_node_empty(self):
        n = self.gdb.node()
        self.assertEqual(n.properties, {})

    def test_create_node_properties_dictionary(self):
        n = self.gdb.node(name="John Doe", profession="Hacker")
        self.assertEqual(n.properties, {"name": "John Doe",
                                        "profession": "Hacker"})

    def test_create_node_dictionary(self):
        n = self.gdb.node(name="John Doe", profession="Hacker")
        self.assertEqual(n["name"], "John Doe")

    def test_create_node_get(self):
        n = self.gdb.node(name="John Doe", profession="Hacker")
        self.assertEqual(n.get("name"), "John Doe")

    def test_create_node_get_default(self):
        n = self.gdb.node(name="John Doe", profession="Hacker")
        self.assertEqual(n.get("surname", "Doe"), "Doe")

    def test_create_node_date(self):
        from neo4jrestclient import options as clientSmartDates
        clientSmartDates.SMART_DATES = True
        dt = datetime.utcnow()
        d = dt.date()
        t = dt.time()
        n = self.gdb.nodes.create(name="John Doe", datetime=dt, date=d, time=t)
        self.assertEqual(n.properties, {"name": "John Doe",
                                        "datetime": dt,
                                        "date": d,
                                        "time": t})
        self.assertEqual(n["datetime"], dt)
        self.assertEqual(n["date"], d)
        self.assertEqual(n["time"], t)
        self.assertEqual(n.get("datetime"), dt)
        self.assertEqual(n.get("date"), d)
        self.assertEqual(n.get("time"), t)
        clientSmartDates.SMART_DATES = False

    def test_get_node(self):
        n1 = self.gdb.nodes.create(name="John Doe", profession="Hacker")
        n2 = self.gdb.nodes.get(n1.id)
        self.assertEqual(n1, n2)

    def test_get_node_url(self):
        n1 = self.gdb.nodes.create(name="John Doe", profession="Hacker")
        n2 = self.gdb.nodes.get(n1.url)
        self.assertEqual(n1, n2)

    def test_get_node_dicionary(self):
        n1 = self.gdb.node(name="John Doe", profession="Hacker")
        n2 = self.gdb.node[n1.id]
        self.assertEqual(n1, n2)

    def test_get_node_dicionary_with_false(self):
        n1 = self.gdb.node(name="John Doe", enable=False)
        n2 = self.gdb.node[n1.id]
        self.assertEqual(n1.properties, n2.properties)

    def test_get_node_url_dicionary(self):
        n1 = self.gdb.node(name="John Doe", profession="Hacker")
        n2 = self.gdb.node[n1.url]
        self.assertEqual(n1, n2)

    def test_set_node_property_dictionary(self):
        n1 = self.gdb.node(name="John Doe", profession="Hacker")
        n1["name"] = "Jimmy Doe"
        n2 = self.gdb.node[n1.id]
        self.assertEqual(n1["name"], n2["name"])

    def test_set_node_property(self):
        n1 = self.gdb.node(name="John Doe", profession="Hacker")
        n1.set("name", "Jimmy Doe")
        n2 = self.gdb.nodes.get(n1.id)
        self.assertEqual(n1.get("name"), n2.get("name"))

    def test_set_node_property_date(self):
        from neo4jrestclient import options as clientSmartDates
        clientSmartDates.SMART_DATES = True
        dt = datetime.utcnow()
        n1 = self.gdb.node(name="John Doe", profession="Hacker")
        n1.set("birthdate", dt)
        n2 = self.gdb.nodes.get(n1.id)
        self.assertEqual(n1.get("birthdate"), dt)
        self.assertEqual(n2.get("birthdate"), dt)
        clientSmartDates.SMART_DATES = False

    def test_set_node_properties(self):
        n1 = self.gdb.node(name="John Doe", profession="Hacker")
        n1.properties = {"name": "Jimmy Doe"}
        n2 = self.gdb.node[n1.id]
        self.assertEqual(n1.properties, n2.properties)

    def test_set_node_properties_numbers_set(self):
        n1 = self.gdb.node()
        properties = {"name": "Jimmy Doe", "age": 30, "active": False}
        n1.properties = properties
        self.assertEqual(n1.properties, properties)

    def test_set_node_property_safe(self):
        n1 = self.gdb.node(language="Español antigüillo")
        n1.set("Idioma de los subtítulos", "Español antigüillo")
        self.assertEqual(n1.get("Idioma de los subtítulos"),
                         n1.get("language"))

    def test_set_node_properties_safe(self):
        n1 = self.gdb.node()
        n1.properties = {"Idioma de los subtítulos": "Español antigüillo"}
        n1_properties = n1.properties
        n2 = self.gdb.node[n1.id]
        n2_properties = n2.properties
        self.assertEqual(n1_properties, n2_properties)

    def test_delete_node_property_dictionary(self):
        n1 = self.gdb.node(name="John Doe", profession="Hacker")
        del n1["name"]
        self.assertEqual(n1.get("name", None), None)

    def test_delete_node_property(self):
        n1 = self.gdb.nodes.create(name="John Doe", profession="Hacker")
        n1.delete("name")
        self.assertEqual(n1.get("name", None), None)

    def test_delete_node_properties(self):
        n1 = self.gdb.node(name="John Doe", profession="Hacker")
        del n1.properties
        self.assertEqual(n1.properties, {})

    def test_delete_node(self):
        n1 = self.gdb.nodes.create(name="John Doe", profession="Hacker")
        identifier = n1.id
        n1.delete()
        try:
            self.gdb.nodes.get(identifier)
            self.fail()
        except (NotFoundError, StatusException):
            pass

    def test_node_hash(self):
        n1 = self.gdb.node()
        n2 = self.gdb.node[n1.id]
        self.assertEqual(len(set([n1, n2])), 1)
        self.assertEqual(hash(n1), hash(n2))
