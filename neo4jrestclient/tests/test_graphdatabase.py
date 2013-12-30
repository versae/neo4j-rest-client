# -*- coding: utf-8 -*-
import unittest
import os

from neo4jrestclient import client


NEO4J_URL = os.environ.get('NEO4J_URL', "http://localhost:7474/db/data/")
NEO4J_VERSION = os.environ.get('NEO4J_VERSION', None)


@unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2"],
                 "Not supported by Neo4j {}".format(NEO4J_VERSION))
class GraphDatabaseTesCase(unittest.TestCase):

    def setUp(self):
        self.url = NEO4J_URL
        self.gdb = client.GraphDatabase(self.url)

    def test_connection_https(self):
        url = NEO4J_URL.replace("http://", "https://")
        url = url.replace(":7474", ":7473")
        client.GraphDatabase(url)

    def test_connection_host(self):
        url = NEO4J_URL.replace("/db/data/", "")
        client.GraphDatabase(url)

    def tearDown(self):
        if self.gdb:
            self.gdb.flush()
