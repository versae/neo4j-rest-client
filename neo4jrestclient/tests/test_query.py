# -*- coding: utf-8 -*-
from datetime import datetime
import unittest
import os

from neo4jrestclient import client
from neo4jrestclient.exceptions import TransactionException
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

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_query_raw_no_return(self):
        property_name = u"rel%s" % text_type(datetime.now().strftime('%s%f'))
        self.gdb.nodes.create(name="John")
        # This sets a property which we will check later
        q = ("""start n=node(*) WHERE HAS(n.name) AND n.name='John' """
             """SET n.`v{}`=True;""".format(property_name))
        # Notice there is NO return value
        self.gdb.query(q=q)
        # Here, we find all nodes that have this property set
        q = ("""start n=node(*) """
             """WHERE HAS(n.`v{}`) return n;""".format(property_name))
        result = self.gdb.query(q=q)
        self.assertTrue(result is not None)
        # Assuming the properties are set according for the first cypher
        # query, this should always be True
        self.assertTrue(len(result) > 0)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_create_node_after_query(self):
        # See https://github.com/versae/neo4j-rest-client/issues/103
        q = """start n=node(*) return n limit 10"""
        self.gdb.query(q=q)
        self.gdb.nodes.create(name="John")

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_query_transaction_reset(self):
        tx = self.gdb.transaction(for_query=True)
        self.assertFalse(tx.finished)
        expires = tx.expires
        tx.reset()
        self.assertNotEqual(expires, tx.expires)
        tx.commit()
        self.assertTrue(tx.finished)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_query_transaction(self):
        tx = self.gdb.transaction(for_query=True)
        self.assertFalse(tx.finished)
        tx.append("CREATE (a) RETURN a")
        results = tx.commit()
        self.assertEqual(len(results), 1)
        for result in results:
            self.assertEqual(len(result), 1)
            self.assertEqual(result.columns, ["a"])
            for row in result:
                self.assertEqual(row[0]['data'], {})
        self.assertTrue(tx.finished)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_query_transaction_object(self):
        tx = self.gdb.transaction(for_query=True)
        tx.append("MERGE (a:Person {name:'Alice'})")
        tx.append("MERGE (b:Person {name:'Bob'})")
        tx.append("MATCH (lft { name: 'Alice' }),(rgt) "
                  "WHERE rgt.name IN ['Bob', 'Carl'] "
                  "CREATE (lft)-[r:KNOWS]->(rgt) "
                  "RETURN r",
                  returns=client.Relationship)
        results = tx.execute()
        self.assertTrue(len(results) == 3)
        self.assertTrue(isinstance(results[-1][0][0], client.Relationship))
        self.assertEqual(results[-1][0][0].type, u"KNOWS")
        # send another three statements and commit the transaction
        tx.append("MERGE (c:Person {name:'Carol'})")
        tx.append("MERGE (d:Person {name:'Dave'})")
        results = tx.commit()
        self.assertTrue(len(results) == 2)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_query_transaction_returns_tuple(self):
        n1 = self.gdb.nodes.create(name="John")
        n2 = self.gdb.nodes.create(name="William")
        rel_type = u"rel%s" % text_type(datetime.now().strftime('%s%f'))
        r = n1.relationships.create(rel_type, n2, since=1982)
        q = """start n=node(*) match n-[r:`{rel}`]-() """ \
            """return n, n.name, r, r.since"""
        params = {
            "rel": rel_type,
        }
        with self.gdb.transaction(for_query=True) as tx:
            results = self.gdb.query(q, params=params,
                                     returns=(client.Node, text_type,
                                              client.Relationship))
        self.assertTrue(tx.finished)
        for node, name, rel, date in results:
            self.assertTrue(node in (n1, n2))
            self.assertTrue(name in (u"John", u"William"))
            self.assertEqual(rel, r)
            self.assertEqual(date, 1982)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_query_transaction_rollback(self):
        with self.gdb.transaction(for_query=True) as tx:
            self.gdb.query("MERGE (a:Person {name:'Alice'})")
            self.gdb.query("MERGE (b:Person {name:'Bob'})")
            results = self.gdb.query(
                "MATCH (lft { name: 'Alice' }),(rgt) "
                "WHERE rgt.name IN ['Bob', 'Carl'] "
                "CREATE (lft)-[r:KNOWS]->(rgt) "
                "RETURN r",
                returns=client.Relationship
            )
            self.assertTrue(len(results) == 1)
            rel = results[0][0]
            self.assertTrue(isinstance(rel, client.Relationship))
            self.assertEqual(rel.type, u"KNOWS")
            tx.rollback()
        self.assertTrue(len(results) == 0)
        self.assertIsNone(self.gdb.relationships.get(rel.id))

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_query_transaction_fails(self):
        try:
            with self.gdb.transaction(for_query=True):
                self.gdb.query("strt n=node(*) return n")
        except Exception as e:
            self.assertTrue(isinstance(e, TransactionException))

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_query_transaction_rollback_after_execute(self):
        tx = self.gdb.transaction(for_query=True)
        tx.append("CREATE (a) RETURN a", returns=client.Node)
        results = tx.execute()
        self.assertTrue(len(results) == 1)
        tx.rollback()
        self.assertTrue(tx.finished)

    @unittest.skipIf(NEO4J_VERSION in ["1.6.3", "1.7.2", "1.8.3", "1.9.7"],
                     "Not supported by Neo4j {}".format(NEO4J_VERSION))
    def test_query_transaction_items_get_populated_after_execute(self):
        tx = self.gdb.transaction(for_query=True)
        tx.append('CREATE (me:User {name: "Me"}) RETURN me;',
                  returns=client.Node)
        results = tx.execute()
        node = results[0][0][0]
        self.assertTrue(node.properties != {})
        self.assertEqual(node["name"], "Me")
        tx.commit()
