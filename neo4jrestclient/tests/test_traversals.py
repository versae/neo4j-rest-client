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


class TraversalsTestCase(GraphDatabaseTesCase):

    def test_create_traversal(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        n1.relationships.create("Knows", n2, since=1970)
        types = [
            client.All.Knows,
        ]
        traversal = n1.traverse(types=types)
        self.assertTrue(len(traversal) > 0)

    def test_path_traversal(self):
        """
        Tests the use of Path as returnable type.
        """
        nodes = [self.gdb.nodes.create() for i in range(10)]
        # Chain them into a linked list
        last = None
        for n in nodes:
            if last is not None:
                last.relationships.create("Knows", n)
            last = n
        # Toss in a different relationship type to ensure the
        # STOP_AT_END_OF_GRAPH didn't break traversing by type
        nodes[-1].relationships.create("Test", self.gdb.nodes.create())
        types = [
            client.All.Knows,
        ]
        stop = constants.STOP_AT_END_OF_GRAPH
        traversal = nodes[0].traverse(types=types, stop=stop,
                                      returns=constants.PATH)
        paths = [path for path in traversal]
        self.assertTrue(len(traversal) > 0)
        self.assertTrue(all([isinstance(path, client.Path) for path in paths]))
        start_node = paths[0].start
        relationship = paths[0].relationships[0]
        self.assertTrue(isinstance(start_node, client.Node))
        self.assertTrue(isinstance(relationship, client.Relationship))

    def test_path_traversal_getitem(self):
        # Test from @shahin: https://gist.github.com/1418704
        n1 = self.gdb.node()
        n2 = self.gdb.node()
        rel = self.gdb.relationships.create(n1, 'knows', n2)

        # Define path traverser
        class PathTraverser(self.gdb.Traversal):
            stop = constants.STOP_AT_END_OF_GRAPH
            returns = constants.PATH
        try:
            paths = [traversal for traversal in PathTraverser(n1)]
            self.assertEqual(len(paths[0]), 1)
        except:
            raise
        finally:
            # Clean up on fail
            self.gdb.relationships.delete(rel.id)
            self.gdb.node.delete(n2.id)
            self.gdb.node.delete(n1.id)

    def test_graph_wide_traversal(self):
        """
        Tests the use of constants.STOP_AT_END_OF_GRAPH as a stop depth.
        """
        nodes = [self.gdb.nodes.create() for i in range(10)]
        # Chain them into a linked list
        last = None
        for n in nodes:
            if last is not None:
                last.relationships.create("Knows", n)
            last = n
        # Toss in a different relationship type to ensure the
        # STOP_AT_END_OF_GRAPH didn't break traversing by type
        nodes[-1].relationships.create("Test", self.gdb.nodes.create())
        types = [
            client.All.Knows,
        ]
        stop = constants.STOP_AT_END_OF_GRAPH
        traversal = nodes[0].traverse(types=types, stop=stop)
        self.assertEqual(len(traversal), len(nodes) - 1)
        # Test an untyple traversal
        traversal = nodes[0].traverse(stop=stop)
        self.assertEqual(len(traversal), len(nodes))

    def test_traversal_return_filter(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        n3 = self.gdb.nodes.create(name='test name')
        n1.KNOWS(n2)
        n2.KNOWS(n3)
        #all traversal
        traversal = n1.traverse(stop=3,
                                returnable=constants.RETURN_ALL_NODES)
        self.assertEqual(len(traversal), 3)
        #all but start traversal
        traversal = n1.traverse(stop=3,
                                returnable=constants.RETURN_ALL_BUT_START_NODE)
        self.assertEqual(len(traversal), 2)
        #custom javascript return filter
        return_filter_body = 'position.endNode().hasProperty("name")&&'\
                             'position.endNode().getProperty("name")=="'\
                             'test name";'
        traversal = n1.traverse(stop=3, returnable=return_filter_body)
        self.assertEqual(len(traversal), 1)

    def test_create_traversal_class(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        n1.relationships.create("Knows", n2, since=1970)

        class TraversalClass(self.gdb.Traversal):

            types = [
                client.All.Knows,
            ]

        results = []
        for result in TraversalClass(n1):
            results.append(result)
        self.assertTrue(len(results) > 0)

    def test_paginated_traversal(self):
        """
        Tests the use of paginated traversals.
        """
        nodes = [self.gdb.nodes.create() for i in range(10)]
        # Chain them into a linked list
        last = None
        for n in nodes:
            if last is not None:
                last.relationships.create("Knows", n)
            last = n
        # Toss in a different relationship type to ensure the
        # STOP_AT_END_OF_GRAPH didn't break traversing by type
        nodes[-1].relationships.create("Test", self.gdb.nodes.create())
        types = [
            client.All.Knows,
        ]
        stop = constants.STOP_AT_END_OF_GRAPH
        pages = nodes[0].traverse(types=types, stop=stop, page_size=5)
        traversal_length = 0
        pages_count = 0
        for traversal in pages:
            traversal_length += len(traversal)
            pages_count += 1
        self.assertEqual(traversal_length, len(nodes) - 1)
        self.assertEqual(pages_count, 2)
        # And make the same test only passing "paginated" argument
        pages = nodes[0].traverse(types=types, stop=stop, paginated=True)
        traversal_length = 0
        for traversal in pages:
            traversal_length += len(traversal)
        self.assertEqual(traversal_length, len(nodes) - 1)
        # Set a ridiculous time_out for getting no results
        pages = nodes[0].traverse(stop=stop, time_out=0.000001)
        traversal_length = len([n for n in [t for t in pages]])
        self.assertEqual(traversal_length, 0)

    # Taken from the official tests by Neo4j python-embedded
    # https://github.com/neo4j/python-embedded
    #        /blob/master/src/test/python/traversal.py
    def create_data(self):
        with self.gdb.transaction():
            self.source = self.gdb.node(message='hello')
            target = self.gdb.node(message='world')
            relationship = self.source.related_to(target, message="graphy")
            secondrel = target.likes(self.source, message="buh")
            relationship
            secondrel

    def test_traverse_string_types(self):
        self.create_data()
        db = self.gdb
        start_node = self.source
        # START SNIPPET: basicTraversal
        traverser = db.traversal()\
            .relationships('related_to')\
            .traverse(start_node)
        # The graph is traversed as
        # you loop through the result.
        for node in traverser.nodes:
            pass
        # END SNIPPET: basicTraversal
        self.assertEqual(len(list(traverser.nodes)), 1)
        # START SNIPPET: directedTraversal
        from neo4jrestclient.traversals import RelationshipDirection
        OUTGOING = RelationshipDirection.OUTGOING
        INCOMING = RelationshipDirection.INCOMING
        #ANY = RelationshipDirection.ANY
        traverser = db.traversal()\
            .relationships('related_to', OUTGOING)\
            .traverse(start_node)
        # END SNIPPET: directedTraversal
        self.assertEqual(len(list(traverser.nodes)), 1)
        traverser = db.traversal()\
            .relationships('related_to', INCOMING)\
            .relationships('likes')\
            .traverse(start_node)
        # END SNIPPET: multiRelationshipTraversal
        self.assertEqual(len(list(traverser.nodes)), 1)
        # START SNIPPET: traversalResults
        traverser = db.traversal()\
            .relationships('related_to')\
            .traverse(start_node)
        # Get each possible path
        for path in traverser:
            pass
        # Get each node
        for node in traverser.nodes:
            pass
        # Get each relationship
        for relationship in traverser.relationships:
            pass
        # END SNIPPET: traversalResults

    def test_traverse_programmatic_types(self):
        from neo4jrestclient.client import Direction
        self.create_data()
        t = self.gdb.traversal()\
            .depthFirst()\
            .relationships(Direction.ANY.related_to)\
            .traverse(self.source)
        res = list(t.nodes)
        self.assertEqual(len(res), 1)

    def test_uniqueness(self):
        self.create_data()
        db = self.gdb
        start_node = self.source
        # START SNIPPET: uniqueness
        from neo4jrestclient.traversals import Uniqueness
        traverser = db.traversal()\
            .uniqueness(Uniqueness.NODE_PATH)\
            .traverse(start_node)
        # END SNIPPET: uniqueness
        res = list(traverser.nodes)
        self.assertEqual(len(res), 2)

    def test_ordering(self):
        self.create_data()
        db = self.gdb
        start_node = self.source
        # START SNIPPET: ordering
        # Depth first traversal, this
        # is the default.
        traverser = db.traversal()\
            .depthFirst()\
            .traverse(self.source)
        # Breadth first traversal
        traverser = db.traversal()\
            .breadthFirst()\
            .traverse(start_node)
        # END SNIPPET: ordering
        res = list(traverser.nodes)
        self.assertEqual(len(res), 1)

    def test_paths(self):
        self.create_data()
        t = self.gdb.traversal()\
            .traverse(self.source)
        for path in t:
            # START SNIPPET: accessPathStartAndEndNode
            start_node = path.start
            end_node = path.end
            # END SNIPPET: accessPathStartAndEndNode
            self.assertNotEqual(start_node, None)
            self.assertNotEqual(end_node, None)
            # START SNIPPET: accessPathLastRelationship
            #last_relationship = path.last_relationship
            # END SNIPPET: accessPathLastRelationship
            # START SNIPPET: loopThroughPath
            for item in path:
                # Item is either a Relationship,
                # or a Node
                pass
            for nodes in path.nodes:
                # All nodes in a path
                pass
            for nodes in path.relationships:
                # All relationships in a path
                pass
            # END SNIPPET: loopThroughPath
            break
