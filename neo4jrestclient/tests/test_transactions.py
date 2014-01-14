# -*- coding: utf-8 -*-
from datetime import datetime
import unittest
import os

from neo4jrestclient import client
from neo4jrestclient import constants


NEO4J_URL = os.environ.get('NEO4J_URL', "http://localhost:7474/db/data/")
NEO4J_VERSION = os.environ.get('NEO4J_VERSION', None)


class GraphDatabaseTesCase(unittest.TestCase):

    def setUp(self):
        self.url = NEO4J_URL
        self.gdb = client.GraphDatabase(self.url)

    def tearDown(self):
        if self.gdb:
            self.gdb.flush()


class TransactionsTestCase(GraphDatabaseTesCase):

    def test_transaction_delete(self):
        n = self.gdb.nodes.create()
        n["age"] = 25
        with self.gdb.transaction():
            n.delete("age")
        self.assertTrue(isinstance(n, client.Node))
        self.assertTrue("age" not in n.properties)

    def test_transaction_delete_node(self):
        n = self.gdb.nodes.create()
        with self.gdb.transaction():
            n.delete()
        self.assertFalse(n)
        self.assertEqual(n, None)

    def test_transaction_delete_relationship(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        r = n1.relationships.create("relation", n2)
        with self.gdb.transaction():
            r.delete()
        self.assertFalse(r)
        self.assertEqual(r, None)

    def test_transaction_properties(self):
        n = self.gdb.nodes.create()
        n["age"] = 25
        n["place"] = "Houston"
        with self.gdb.transaction():
            n.delete("age")
        self.assertTrue(isinstance(n, client.Node))
        self.assertTrue("age" not in n.properties)
        self.assertTrue("place" in n.properties)

    def test_transaction_properties_update(self):
        n = self.gdb.nodes.create()
        n["age"] = 25
        with self.gdb.transaction(update=False):
            n.delete("age")
        self.assertTrue(isinstance(n, client.Node))
        self.assertTrue("age" in n.properties)

    def test_transaction_create(self):
        with self.gdb.transaction():
            n = self.gdb.nodes.create(age=25)
        self.assertTrue(isinstance(n, client.Node))
        self.assertTrue(n.get("age", True))

    def test_transaction_create_and_set(self):
        with self.gdb.transaction():
            n = self.gdb.nodes.create(age=25)
            n.set("surname", u"AC/DC")
            n["name"] = u"Motörhead"
            self.assertEqual(n.properties, {
                "age": 25,
                "name": u"Motörhead",
                "surname": u"AC/DC",
            })
        self.assertTrue(isinstance(n, client.Node))
        self.assertEqual(n.get("age"), 25)
        self.assertEqual(n.get("name"), u"Motörhead")
        self.assertEqual(n.properties, {
            "age": 25,
            "name": u"Motörhead",
            "surname": u"AC/DC",
        })

    def test_transaction_get(self):
        n = self.gdb.nodes.create()
        n1 = self.gdb.nodes.get(n.id)
        with self.gdb.transaction():
            n2 = self.gdb.nodes.get(n.id)
        self.assertTrue(isinstance(n1, client.Node))
        self.assertTrue(isinstance(n2, client.Node))
        self.assertEqual(n1, n2)

    def test_transaction_property(self):
        n = self.gdb.nodes.create()
        with self.gdb.transaction():
            n["age"] = 25
        self.assertTrue(isinstance(n, client.Node))
        self.assertTrue("age" in n.properties)

    def test_transaction_relationship(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        with self.gdb.transaction():
            r = n1.relationships.create("Knows", n2, since=1970)
        self.assertTrue(isinstance(r, client.Relationship))
        self.assertTrue(r is not None)

    def test_transaction_commit(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        initial_rels = len(n1.relationships)
        rels_number = 10
        with self.gdb.transaction(commit=False) as tx:
            for i in range(1, 1 + rels_number):
                n1.relationships.create("relation_%s" % i, n2)
        pre_commit_rels = len(n1.relationships)
        self.assertEqual(initial_rels, pre_commit_rels)
        tx.commit()
        post_commit_rels = len(n1.relationships)
        self.assertEqual(initial_rels + rels_number, post_commit_rels)

    def test_transaction_globals(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        initial_rels = len(n1.relationships)
        rels_number = 10
        with self.gdb.transaction(using_globals=False) as tx:
            for i in range(1, 1 + rels_number):
                n1.relationships.create("relation_%s" % i, n2, tx=tx)
        self.assertEqual(initial_rels + rels_number, len(n1.relationships))

    def test_transaction_update(self):
        n = self.gdb.nodes.create()
        n["age"] = 25
        with self.gdb.transaction(update=False):
            n.delete("age")
        self.assertTrue(isinstance(n, client.Node))
        self.assertTrue("age" in n.properties)
        n.update()
        self.assertTrue("age" not in n.properties)

    def test_transaction_set(self):
        n = self.gdb.nodes.create()
        n["age"] = 25
        n["name"] = "John"
        n["place"] = "Houston"
        with self.gdb.transaction(commit=False, using_globals=False) as tx:
            n["name"] = tx("Jonathan")
            n["age", tx] = 30
            n.set("place", "Toronto", tx=tx)
        self.assertEqual(n["age"], 25)
        self.assertEqual(n["name"], "John")
        self.assertEqual(n["place"], "Houston")
        tx.commit()
        self.assertEqual(n["age"], 30)
        self.assertEqual(n["name"], "Jonathan")
        self.assertEqual(n["place"], "Toronto")

    def test_transaction_multiple(self):
        n = self.gdb.nodes.create()
        n["age"] = 25
        n["name"] = "John"
        n["place"] = "Houston"
        with self.gdb.transaction(commit=False, using_globals=False) as t1:
            with self.gdb.transaction(commit=False, using_globals=False) as t2:
                n.delete("age", tx=t1)
                n["name"] = t2("Jonathan")
                n["place", t2] = "Toronto"
        self.assertTrue("age" in n.properties)
        t1.commit()
        self.assertTrue("age" not in n.properties)
        self.assertEqual(n["name"], "John")
        self.assertEqual(n["place"], "Houston")
        t2.commit()
        self.assertEqual(n["name"], "Jonathan")
        self.assertEqual(n["place"], "Toronto")

    def test_transaction_list(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        initial_rels = len(n1.relationships)
        relations = []
        rels_number = 10
        with self.gdb.transaction(commit=False) as tx:
            for i in range(1, 1 + rels_number):
                relation = n1.relationships.create("relation_%s" % i, n2)
                relations.append(relation)
        tx.commit()
        self.assertEqual(initial_rels + rels_number, len(n1.relationships))
        self.assertTrue(all([isinstance(r, client.Relationship)]
                            for r in relations))

    def test_transaction_dict(self):
        nodes = {}
        nodes_number = 10
        with self.gdb.transaction():
            for i in range(1, 1 + nodes_number):
                nodes[i] = self.gdb.nodes.create(position=i)
        for position, node in nodes.items():
            self.assertTrue(isinstance(node, client.Node))
            self.assertEqual(position, node["position"])

    def test_transaction_conections(self):
        from neo4jrestclient import options as clientDebug
        clientDebug.DEBUG = True
        id_list = []
        for i in range(5):
            n = self.gdb.nodes.create(number=i)
            id_list.append(n.id)
        nodes = []
        with self.gdb.transaction(commit=False) as tx:
            for i in id_list:
                nodes.append(self.gdb.node[i])
        tx.commit()
        clientDebug.DEBUG = False

    def test_transaction_create_relationship_functional(self):
        with self.gdb.transaction():
            n1 = self.gdb.node()
            n2 = self.gdb.node()
            rel = n1.relationships.create("Knows", n2)
            rel["when"] = "January"
        self.assertEqual(rel.properties, {"when": "January"})

    def test_transaction_create_relationship_functional_mixed1(self):
        n1 = self.gdb.node()
        with self.gdb.transaction():
            n2 = self.gdb.node()
            rel = n1.relationships.create("Knows", n2)
            rel["when"] = "January"
        self.assertEqual(rel.properties, {"when": "January"})

    def test_transaction_create_relationship_functional_mixed2(self):
        n2 = self.gdb.node()
        with self.gdb.transaction():
            n1 = self.gdb.node()
            rel = n1.relationships.create("Knows", n2)
            rel["when"] = "January"
        self.assertEqual(rel.properties, {"when": "January"})

    def test_transaction_create_relationship_functional2(self):
        with self.gdb.transaction():
            n1 = self.gdb.node()
            n2 = self.gdb.node()
            rel = n1.relationships.create("Knows", n2)
            rel["when"] = "January"
            self.assertEqual(rel.start, n1)
            self.assertEqual(rel.end, n2)
        self.assertEqual(rel.properties, {"when": "January"})
        self.assertTrue(isinstance(n1, client.Node))
        self.assertTrue(isinstance(n2, client.Node))

    def test_transaction_create_relationship(self):
        with self.gdb.transaction():
            n1 = self.gdb.node()
            n2 = self.gdb.node()
            rel = n1.Knows(n2)
            rel["when"] = "January"
        self.assertEqual(rel.properties, {"when": "January"})

    # The next tests for transaction were taken from @mhluongo fork
    # https://github.com/mhluongo/neo4j-rest-client
    #        /blob/master/neo4jrestclient/tests.py
    def test_transaction_index_creation(self):
        """
        Tests whether indexes are properly created during a transaction.
        Asserts the creation also behaves transactionally (ie, not until
        commit).
        """
        with self.gdb.transaction():
            i1 = self.gdb.nodes.indexes.create('index_from_tx')
            transactionality_test = i1()
        self.assertTrue(isinstance(transactionality_test, dict))
        self.assertTrue(i1 is not None)
        self.assertTrue(isinstance(i1, client.Index))
        i2 = self.gdb.nodes.indexes.get('index_from_tx')
        self.assertTrue(i1 == i2)

    def test_transaction_add_node_to_index(self):
        """
        Tests whether a node can be added to an index within a transaction.
        Does not assert transactionality.
        """
        n1 = self.gdb.nodes.create()
        index = self.gdb.nodes.indexes.create('index_nodes')
        with self.gdb.transaction():
            index.add('test1', 'test1', n1)
            index['test2']['test2'] = n1
        self.assertTrue(index['test1']['test1'][-1] == n1)
        self.assertTrue(index['test2']['test2'][-1] == n1)

    def test_transaction_index_add_rel_to_index(self):
        """
        Tests whether a relationship can be added to an index within a
        transaction.
        Does not assert transactionality.
        """
        #test nodes
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        r = n1.relationships.create('Knows', n2)
        index = self.gdb.relationships.indexes.create('index_rel')
        with self.gdb.transaction():
            index.add('test1', 'test1', r)
            index['test2']['test2'] = r
        self.assertTrue(index['test1']['test1'][-1] == r)
        self.assertTrue(index['test2']['test2'][-1] == r)

    def test_transaction_index_query(self):
        """
        Tests whether the transaction methods work with index queries.
        Note- this test does not prove query transactionality.
        """
        n1 = self.gdb.nodes.create()
        index = self.gdb.nodes.indexes.create('index2')
        index.add('test2', 'test2', n1)
        # Test getting nodes from index during transaction
        tx = self.gdb.transaction()
        index_hits = index['test2']['test2']
        tx.commit()
        self.assertTrue(n1 == index_hits[-1])

    def test_transaction_remove_node_from_index(self):
        index = self.gdb.nodes.indexes.create('index3')
        n = self.gdb.nodes.create()
        index.add('test3', 'test3', n)
        tx = self.gdb.transaction(using_globals=False)
        index.delete('test3', 'test3', n, tx=tx)
        # Assert transactional
        self.assertTrue(n in index['test3']['test3'])
        tx.commit()
        self.assertTrue(n not in index['test3']['test3'])

    def test_transaction_query_index_for_new_node(self):
        #test nodes created in transaction

        index_name = 'index4%s' % datetime.now().strftime('%s%f')
        index = self.gdb.nodes.indexes.create(index_name)
        tx = self.gdb.transaction(using_globals=False)
        n4 = self.gdb.nodes.create(tx=tx)
        index.add('test3', 'test3', n4, tx=tx)
        # Assert transactional
        transactional = True
        try:
            index['test3']['test3'][0]
            transactional = False
        except:
            pass
        tx.commit()
        self.assertTrue(transactional)
        self.assertTrue(index['test3']['test3'][-1] == n4)

    def test_transaction_add_to_new_index(self):
        """
        Tests whether a node can be added to an index that was created earlier
        in the transaction.
        Does not assert transactionality.
        """
        n1 = self.gdb.nodes.create()
        tx = self.gdb.transaction()
        index = self.gdb.nodes.indexes.create('index5')
        index.add('test1', 'test1', n1)
        tx.commit()
        self.assertTrue(isinstance(index, client.Index))
        self.assertTrue(index['test1']['test1'][-1] == n1)

    def test_transaction_new_node_properties(self):
        """
        Tests setting properties on a node created within the same tx.
        Doesn't show transactionality.
        """
        def has_props(node):
            return n['name'] == 'test' and n['age'] == 0

        tx = self.gdb.transaction()
        n = self.gdb.node()
        n['name'] = 'test'
        n['age'] = 0
        tx_props_kept = has_props(n)
        tx.commit()
        self.assertTrue(tx_props_kept)
        self.assertTrue(has_props(n))

    def test_transaction_properties_class(self):
        def has_props(node):
            return node['test1'] == 'test1' and node['test2'] == 'test2'

        def set_props(node):
            node['test1'] = 'test1'
            node['test2'] = 'test2'

        n1 = self.gdb.node()
        tx = self.gdb.transaction()
        set_props(n1)
        has_props_before_commit = has_props(n1)
        tx.commit()
        self.assertFalse(has_props_before_commit)
        self.assertTrue(has_props(n1))
        tx = self.gdb.transaction()
        n2 = self.gdb.node()
        set_props(n2)
        has_props_before_commit = has_props(n1)
        tx.commit()
        self.assertFalse(has_props_before_commit)
        self.assertTrue(has_props(n2))

    def test_transaction_traversal(self):
        nodes = [self.gdb.nodes.create() for i in range(10)]
        # Chain them into a linked list
        last = None
        for n in nodes:
            if last is not None:
                last.relationships.create("Knows", n)
            last = n

        with self.gdb.transaction():
            tx_n = self.gdb.node()
            last.relationships.create('Knows', tx_n)
            types = [
                client.All.Knows,
            ]
            stop = constants.STOP_AT_END_OF_GRAPH
            traversal = nodes[0].traverse(types=types, stop=stop)

        # a non-transactional traversal will be 1 node short
        self.assertEqual(len(traversal), len(nodes) - 1)

    def test_transaction_create_1000_nodes_relationship(self):
        TAG_DICT = {}
        EDGE_DICT = {}
        operations = 0
        with self.gdb.transaction() as tx:
            for i in range(1, 1000):
                operations = len(tx.operations)
                id1 = i
                id2 = i + 1
                TAG_DICT[id1] = self.gdb.node.create(tag="tag1")
                TAG_DICT[id2] = self.gdb.node.create(tag="tag2")
                RUN = self.gdb.node.create(name="RUN")
                if not (id1, id2) in EDGE_DICT:
                    edge = self.gdb.node(name='EDGE_%04d_%04d' % (id1, id2),
                                         type='edge', tag1=id1, tag2=id2)
                    tag1 = TAG_DICT[id1]
                    tag2 = TAG_DICT[id2]
                    edge.relationships.create("EDGE_TAG", tag1)
                    edge.relationships.create("EDGE_TAG", tag2)
                    RUN.relationships.create("RUN_EDGE", edge)
                    EDGE_DICT[(id1, id2)] = edge
                else:
                    edge = EDGE_DICT[(id1, id2)]
        self.assertTrue(operations >= i)

    def test_transaction_access_node(self):
        frame = self.gdb.node.create()
        with self.gdb.transaction():
            edge = self.gdb.node(name='EDGE')
        rel = frame.FRAME_EDGE(edge)
        self.assertTrue(isinstance(rel, client.Relationship))

    # Test from http://stackoverflow.com/questions/11407546/
    def test_transaction_index_access_create_relationship(self):
        s = self.gdb.node.create(id=1)
        d = self.gdb.node.create(id=2)
        nidx = self.gdb.nodes.indexes.create('nodelist')
        nidx.add('nid', 1, s)
        nidx.add('nid', 2, d)
        nodelist = [(1, 2)]
        with self.gdb.transaction():
            for s_id, d_id in nodelist:
                sn = nidx['nid'][s_id][-1]
                dn = nidx['nid'][d_id][-1]
#                rel = sn.Follows(dn)
#        self.assertTrue(isinstance(rel, client.Relationship))
        self.assertEqual(s, sn)
        self.assertEqual(d, dn)

    # Test from https://github.com/versae/neo4j-rest-client/issues/69
    def test_transaction_split(self):

        with self.gdb.transaction():
            a = self.gdb.nodes.create(name='a')
            b = self.gdb.nodes.create(name='b')

        with self.gdb.transaction():
            a.relationships.create("Test", b)
            c = self.gdb.nodes.create(name='c')
            b.relationships.create("Test", c)
            c.relationships.create("Test", a)

        a = self.gdb.nodes[a.id]
        b = self.gdb.nodes[b.id]
        c = self.gdb.nodes[c.id]

        rel_ab = a.relationships.outgoing()[0]
        assert(rel_ab.start == a and rel_ab.end == b)

        rel_bc = b.relationships.outgoing()[0]
        assert(rel_bc.start == b and rel_bc.end == c)

        rel_ca = c.relationships.outgoing()[0]
        assert(rel_ca.start == c and rel_ca.end == a)
