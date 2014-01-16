# -*- coding: utf-8 -*-
from datetime import datetime
import unittest
import os

from neo4jrestclient import client
from neo4jrestclient.exceptions import NotFoundError, StatusException
from neo4jrestclient.utils import PY2


NEO4J_URL = os.environ.get('NEO4J_URL', "http://localhost:7474/db/data/")
NEO4J_VERSION = os.environ.get('NEO4J_VERSION', None)


class GraphDatabaseTesCase(unittest.TestCase):

    def setUp(self):
        self.url = NEO4J_URL
        self.gdb = client.GraphDatabase(self.url)

    def tearDown(self):
        if self.gdb:
            self.gdb.flush()


class IndicesTestCase(GraphDatabaseTesCase):

    def test_create_index_for_nodes(self):
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        index = self.gdb.nodes.indexes.create(name="doe")
        index["surnames"]["d"] = n1
        self.assertTrue(n1 in index["surnames"]["d"])

    def test_create_index_for_nodes_and_dots(self):
        # From https://github.com/versae/neo4j-rest-client/issues/43
        n1 = self.gdb.nodes.create(name="John.Doe", place="Texas.s")
        index = self.gdb.nodes.indexes.create(name="dots")
        index["surnames.s"]["d.d"] = n1
        self.assertTrue(n1 in index["surnames.s"]["d.d"])

    def test_create_index_for_nodes_unicode(self):
        n1 = self.gdb.nodes.create(name="Lemmy", band="Motörhead")
        index = self.gdb.nodes.indexes.create(name="doe")
        index["bands"]["Motörhead"] = n1
        self.assertTrue(n1 in index["bands"]["Motörhead"])

    def test_create_index_for_nodes_and_boolean(self):
        n1 = self.gdb.nodes.create(name="John", is_real=True, is_fake=False)
        index = self.gdb.nodes.indexes.create(name="boolean")
        index["is_real"][True] = n1
        index["is_fake"][False] = n1
        self.assertTrue(n1 in index["is_real"][True])
        self.assertTrue(n1 in index["is_fake"][False])

    def test_create_index_for_nodes_and_number(self):
        n1 = self.gdb.nodes.create(name="John", age=30, mean=2.7)
        index = self.gdb.nodes.indexes.create(name="number")
        index["age"][30] = n1
        index["mean"][2.7] = n1
        self.assertTrue(n1 in index["age"][30])
        self.assertTrue(n1 in index["mean"][2.7])

    def test_create_index_for_nodes_and_unicode(self):
        index = self.gdb.nodes.indexes.create(name="unicode")
        n1 = self.gdb.nodes.create(name="First")
        key = u"Profesión"
        value = u"Înformáticö"
        n1.set(key, value)
        index[key][value] = n1
        self.assertTrue(n1 in index[key][value])
        n2 = self.gdb.nodes.create(name="Second")
        key = u"Título/Nombre"
        value = u"Necronomicón"
        n2.set(key, value)
        index[key][value] = n2
        self.assertTrue(n2 in index[key][value])

    def test_create_index_for_nodes_url_safe(self):
        n1 = self.gdb.nodes.create(name="Brian", place="AC/DC")
        index = self.gdb.nodes.indexes.create(name="doe")
        index["bands"]["AC/DC"] = n1
        self.assertTrue(n1 in index["bands"]["AC/DC"])

    def test_delete_index_for_nodes(self):
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        index = self.gdb.nodes.indexes.create(name="doe")
        index["surnames"]["d"] = n1
        index.delete()
        self.assertRaises(NotFoundError,
                          index["surnames"].__getitem__, "d")

    def test_create_index_for_relationships(self):
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        n2 = self.gdb.nodes.create(name="Michael Doe", place="Tijuana")
        r1 = self.gdb.relationships.create(n1, "Hates", n2)
        index = self.gdb.relationships.indexes.create(name="brothers")
        index["feeling"]["hate"] = r1
        self.assertTrue(r1 in index["feeling"]["hate"])

    def test_delete_node_from_index(self):
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        index = self.gdb.nodes.indexes.create(name="doe")
        index["surnames"]["d"] = n1
        index.delete("surnames", "d", n1)
        self.assertTrue(n1 not in index["surnames"]["d"])

    def test_delete_node_from_index_with_no_value(self):
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        index = self.gdb.nodes.indexes.create(name="doe")
        index["surnames"]["d"] = n1
        index.delete("surnames", None, n1)
        self.assertTrue(n1 not in index["surnames"]["d"])

    def test_delete_node_from_index_with_no_value_nor_key(self):
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        index = self.gdb.nodes.indexes.create(name="doe")
        index["surnames"]["d"] = n1
        index.delete(None, None, n1)
        self.assertTrue(n1 not in index["surnames"]["d"])

    def test_delete_relationship_from_index(self):
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        n2 = self.gdb.nodes.create(name="Michael Doe", place="Tijuana")
        r1 = self.gdb.relationships.create(n1, "Hates", n2)
        index = self.gdb.relationships.indexes.create(name="brothers")
        index["feeling"]["hate"] = r1
        index.delete("feeling", "hate", r1)
        self.assertTrue(r1 not in index["feeling"]["hate"])

    def test_delete_index_for_relationships(self):
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        n2 = self.gdb.nodes.create(name="Michael Doe", place="Tijuana")
        r1 = self.gdb.relationships.create(n1, "Hates", n2)
        index = self.gdb.relationships.indexes.create(name="brothers")
        index["feeling"]["hate"] = r1
        index.delete()
        self.assertRaises(NotFoundError,
                          index["feeling"].__getitem__, "hate")

    @unittest.skipIf(not PY2,
                     "Lucene Query Builder is not Python3 compliant yet")
    def test_query_index(self):
        Q = client.Q
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        n2 = self.gdb.nodes.create(name="Michael Donald", place="Tijuana")
        index = self.gdb.nodes.indexes.create(name="do", type="fulltext")
        index["surnames"]["doe"] = n1
        index["surnames"]["donald"] = n2
        index['place']['Texas'] = n1
        index['place']['Tijuana'] = n2
        results = index.query("surnames", "do*")
        self.assertTrue(n1 in results and n2 in results)
        results = index.query("surnames:do*")
        self.assertTrue(n1 in results and n2 in results)
        results = index.query('surnames', Q('do*', wildcard=True))
        self.assertTrue(n1 in results and n2 in results)
        results = index.query(Q('surnames', 'do*', wildcard=True))
        self.assertTrue(n1 in results and n2 in results)
        results = index.query(Q('surnames', 'do*', wildcard=True)
                              & Q('place', 'Tijuana'))
        self.assertTrue(n1 not in results and n2 in results)
        results = index.query(-Q('surnames', 'donald') | +Q('place', 'Texas'))
        self.assertTrue(n2 not in results and n1 in results)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_index_get_or_create_created(self):
        index = self.gdb.nodes.indexes.create(name="doe")
        properties = {
            "name": "Lemmy",
            "band": "Motörhead",
        }
        n1 = index.get_or_create(key="bands", value="Motörhead",
                                 properties=properties)
        self.assertTrue(n1 in index["bands"]["Motörhead"])

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_index_get_or_create_existing(self):
        index = self.gdb.nodes.indexes.create(name="doe")
        now = datetime.now().strftime('%s%f')
        properties = {
            "name": "Lemmy",
            "band": "Motörhead",
            "now": now,
        }
        n1 = self.gdb.nodes.create(**properties)
        index["now"][now] = n1
        n2 = index.get_or_create(key="now", value=now,
                                 properties=properties)
        self.assertEqual(n1, n2)
        self.assertTrue(n1 in index["now"][now])
        self.assertTrue(n2 in index["now"][now])

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_index_create_or_fail_created(self):
        index = self.gdb.nodes.indexes.create(name="doe")
        properties = {
            "name": "Lemmy",
            "band": "Motörhead",
        }
        n1 = index.create_or_fail(key="bands", value="Motörhead",
                                  properties=properties)
        self.assertTrue(n1 in index["bands"]["Motörhead"])

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_index_create_or_fail_existing(self):
        index = self.gdb.nodes.indexes.create(name="doe")
        now = datetime.now().strftime('%s%f')
        properties = {
            "name": "Lemmy",
            "band": "Motörhead",
            "now": now,
        }
        n1 = self.gdb.nodes.create(**properties)
        index["now"][now] = n1
        self.assertRaises((Exception, ValueError, StatusException),
                          index.create_or_fail,
                          key="now", value=now, properties=properties)
