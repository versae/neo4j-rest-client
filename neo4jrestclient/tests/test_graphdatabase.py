# -*- coding: utf-8 -*-
import unittest
import os

from neo4jrestclient import client


NEO4J_URL = os.environ.get('NEO4J_URL', "http://localhost:7474/db/data/")
NEO4J_VERSION = os.environ.get('NEO4J_VERSION', None)


class GraphDatabaseTesCase(unittest.TestCase):

    def setUp(self):
        self.url = NEO4J_URL
        self.gdb = client.GraphDatabase(self.url)

    def test_connection_https(self):
        url = NEO4J_URL.replace("http://", "https://")
        url = url.replace(":7474", ":7473")
        client.GraphDatabase(url)

    def tearDown(self):
        if self.gdb:
            self.gdb.flush()
