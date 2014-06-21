# -*- coding: utf-8 -*-
from datetime import datetime
from random import randint
import unittest
import os

from neo4jrestclient import constants
from neo4jrestclient import client
from neo4jrestclient import query
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


class FilterTestCase(GraphDatabaseTesCase):

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_filter_nodes(self):
        Q = query.Q
        for i in range(5):
            self.gdb.nodes.create(name="William %s" % i)
        lookup = Q("name", istartswith="william")
        williams = self.gdb.nodes.filter(lookup)
        self.assertTrue(len(williams) >= 5)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_filter_nodes_complex_lookups(self):
        Q = query.Q
        for i in range(5):
            self.gdb.nodes.create(name="James", surname="Smith %s" % i)
        lookups = (
            Q("name", exact="James") &
            (Q("surname", startswith="Smith") &
             ~Q("surname", endswith="1"))
        )
        williams = self.gdb.nodes.filter(lookups)
        self.assertTrue(len(williams) >= 4)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_filter_nodes_slicing(self):
        Q = query.Q
        for i in range(5):
            self.gdb.nodes.create(name="William %s" % i)
        lookup = Q("name", istartswith="william")
        williams = self.gdb.nodes.filter(lookup)[:4]
        self.assertTrue(len(williams) == 4)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_filter_nodes_ordering(self):
        Q = query.Q
        for i in range(5):
            self.gdb.nodes.create(name="William", code=i)
        lookup = Q("code", gte=2)
        williams = self.gdb.nodes.filter(lookup).order_by("code",
                                                          constants.DESC)
        self.assertTrue(williams[-1]["code"] > williams[0]["code"])

    @unittest.skipIf(NEO4J_VERSION not in ["1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_filter_nodes_nullable(self):
        Q = query.Q
        for i in range(5):
            self.gdb.nodes.create(name="William %s" % i)
        lookup = Q("name", istartswith="william", nullable=False)
        williams = self.gdb.nodes.filter(lookup)[:10]
        self.assertTrue(len(williams) > 5)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_filter_nodes_start(self):
        Q = query.Q
        nodes = []
        for i in range(5):
            nodes.append(self.gdb.nodes.create(name="William %s" % i))
        lookup = Q("name", istartswith="william")
        williams = self.gdb.nodes.filter(lookup, start=nodes)
        self.assertTrue(len(williams) == 5)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_filter_nodes_start_index(self):
        Q = query.Q
        t = text_type(datetime.now().strftime('%s%f'))
        index_name = "filter_nodes_start_index_%s" % t
        index = self.gdb.nodes.indexes.create(name=index_name)
        for i in range(5):
            n = self.gdb.nodes.create(name="William %s" % i)
            index["name"]["William"] = n
        lookup = Q("name", istartswith="william")
        williams = self.gdb.nodes.filter(lookup, start=index)
        self.assertTrue(len(williams) == 5)
        williams = self.gdb.nodes.filter(lookup, start=index["name"])
        self.assertTrue(len(williams) == 5)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_filter_index_for_nodes(self):
        Q = query.Q
        n1 = self.gdb.nodes.create(name="Lemmy", band="Motörhead")
        index = self.gdb.nodes.indexes.create(name="music")
        index["bandś"]["Motörhead"] = n1
        lookup = Q("name", icontains='Lemmy')
        self.assertTrue(n1 in index.filter(lookup))
        self.assertTrue(n1 in index.filter(lookup, key="bandś"))
        self.assertTrue(n1 in index.filter(lookup, key="bandś",
                                           value="Motörhead"))
        self.assertTrue(n1 in index["bandś"].filter(lookup))
        self.assertTrue(n1 in index["bandś"].filter(lookup, value="Motörhead"))

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_filter_index_for_relationships(self):
        Q = query.Q
        n1 = self.gdb.nodes.create(name="Jóhn Doe", place="Texaś")
        n2 = self.gdb.nodes.create(name="Míchael Doe", place="Tíjuana")
        r1 = self.gdb.relationships.create(n1, "Hateś", n2, since=1995)
        index = self.gdb.relationships.indexes.create(name="bróthers")
        index["feelińg"]["háte"] = r1
        lookup = Q("since", lte=2000)
        self.assertTrue(r1 in index.filter(lookup))
        self.assertTrue(r1 in index.filter(lookup, key="feelińg"))
        self.assertTrue(r1 in index.filter(lookup, key="feelińg",
                                           value="háte"))
        self.assertTrue(r1 in index["feelińg"].filter(lookup))
        self.assertTrue(r1 in index["feelińg"].filter(lookup, value="háte"))

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_filter_relationships_start(self):
        Q = query.Q
        rels = []
        for i in range(5):
            n1 = self.gdb.nodes.create(name="William %s" % i)
            n2 = self.gdb.nodes.create(name="Rose %s" % i)
            r = n1.loves(n2, since=(1990 + i))
            rels.append(r)
        lookup = Q("since", lte=2000)
        old_loves = self.gdb.relationships.filter(lookup, start=rels)
        self.assertTrue(len(old_loves) >= 5)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_filter_relationships_start_index(self):
        Q = query.Q
        t = text_type(datetime.now().strftime('%s%f'))
        index_name = "filter_relationships_start_index_%s" % t
        index = self.gdb.relationships.indexes.create(name=index_name)
        for i in range(5):
            n1 = self.gdb.nodes.create(name="William %s" % i)
            n2 = self.gdb.nodes.create(name="Rose %s" % i)
            r = n1.loves(n2, since=(1990 + i))
            index["since"][1990] = r
        lookup = Q("since", lte=2000)
        old_loves = self.gdb.relationships.filter(lookup, start=index)
        self.assertTrue(len(old_loves) == 5)
        old_loves = self.gdb.relationships.filter(lookup, start=index["since"])
        self.assertTrue(len(old_loves) == 5)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_filter_inrange(self):
        Q = query.Q
        t1 = randint(1, 10 ** 10)
        t2 = t1 + 1
        for i in range(5):
            self.gdb.nodes.create(number=t1)
            self.gdb.nodes.create(number=t2)
        lookup = Q("number", inrange=[t1, t2])
        nodes = self.gdb.nodes.filter(lookup)
        self.assertTrue(len(nodes) == 10)
