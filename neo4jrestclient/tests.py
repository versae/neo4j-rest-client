# -*- coding: utf-8 -*-
from datetime import datetime
try:
    import cPickle as pickle
except:
    import pickle

import client
import constants
import request
import unittest


class NodesTestCase(unittest.TestCase):

    def setUp(self):
        self.url = "http://localhost:7474/db/data/"
        self.gdb = client.GraphDatabase(self.url)

    def tearDown(self):
        if self.gdb:
            self.gdb.flush()

    def test_connection_cache(self):
        import options as clientCache
        clientCache.CACHE = True
        gdb = client.GraphDatabase(self.url)
        clientCache.CACHE = False
        self.assertEqual(gdb.url, self.url)

    def test_connection_debug(self):
        import options as clientDebug
        clientDebug.DEBUG = True
        gdb = client.GraphDatabase(self.url)
        clientDebug.DEBUG = False
        self.assertEqual(gdb.url, self.url)

    def test_connection_cache_debug(self):
        import options as clientCacheDebug
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

    def test_set_node_properties(self):
        n1 = self.gdb.node(name="John Doe", profession="Hacker")
        n1.properties = {"name": "Jimmy Doe"}
        n2 = self.gdb.node[n1.id]
        self.assertEqual(n1.properties, n2.properties)

    def test_set_node_property_safe(self):
        n1 = self.gdb.node(language="Español antigüillo")
        n1.set("Idioma de los subtítulos", "Español antigüillo")
        self.assertEqual(n1.get("Idioma de los subtítulos"), n1.get("language"))

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
        except request.NotFoundError, request.StatusException:
            pass

    def test_node_hash(self):
        n1 = self.gdb.node()
        n2 = self.gdb.node[n1.id]
        self.assertEqual(len(set([n1, n2])), 1)
        self.assertEqual(hash(n1), hash(n2))


class RelationshipsTestCase(NodesTestCase):

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
        self.assertRaises(request.NotFoundError, self.gdb.relationships.get,
                          rel_id)


class IndexesTestCase(RelationshipsTestCase):

    def test_create_index_for_nodes(self):
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        index = self.gdb.nodes.indexes.create(name="doe")
        index["surnames"]["d"] = n1
        self.assertTrue(n1 in index["surnames"]["d"])

    def test_create_index_for_nodes_and_dots(self):
        # From https://github.com/versae/neo4j-rest-client/issues/43
        n1 = self.gdb.nodes.create(name="John.Doe", place="Texas.s")
        index = self.gdb.nodes.indexes.create(name="doe")
        index["surnames.s"]["d.d"] = n1
        self.assertTrue(n1 in index["surnames.s"]["d.d"])

    def test_create_index_for_nodes_unicode(self):
        n1 = self.gdb.nodes.create(name="Lemmy", band="Motörhead")
        index = self.gdb.nodes.indexes.create(name="doe")
        index["bands"]["Motörhead"] = n1
        self.assertTrue(n1 in index["bands"]["Motörhead"])

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
        self.assertRaises(request.NotFoundError,
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
        self.assertRaises(request.NotFoundError,
                          index["feeling"].__getitem__, "hate")

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


class TraversalsTestCase(IndexesTestCase):

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
        nodes = [self.gdb.nodes.create() for i in xrange(10)]
        # Chain them into a linked list
        last = None
        for n in nodes:
            if last:
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
        rel = self.gdb.relationships.create(n1,'knows',n2)
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
        nodes = [self.gdb.nodes.create() for i in xrange(10)]
        # Chain them into a linked list
        last = None
        for n in nodes:
            if last:
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
        traversal = n1.traverse(stop=3,\
                                returnable=constants.RETURN_ALL_NODES)
        self.assertEqual(len(traversal), 3)
        #all but start traversal
        traversal = n1.traverse(stop=3,\
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
        import options as clientDebug
        clientDebug.DEBUG = False
        nodes = [self.gdb.nodes.create() for i in xrange(10)]
        # Chain them into a linked list
        last = None
        for n in nodes:
            if last:
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
    # https://github.com/neo4j/python-embedded/blob/master/src/test/python/traversal.py
    def create_data(self):
        with self.gdb.transaction():
            self.source = self.gdb.node(message='hello')
            target = self.gdb.node(message='world')
            relationship = self.source.related_to(target, message="graphy")
            secondrel = target.likes(self.source, message="buh")

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
        from traversals import RelationshipDirection
        OUTGOING = RelationshipDirection.OUTGOING
        INCOMING = RelationshipDirection.INCOMING
        ANY = RelationshipDirection.ANY
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
        from client import Direction
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
        from traversals import Uniqueness
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
            last_relationship = path.last_relationship
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


class ExtensionsTestCase(TraversalsTestCase):

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

    def test_gremlin_extension_reference_node(self):
        # Assuming the GremlinPlugin installed
        ext = self.gdb.extensions.GremlinPlugin
        n = ext.execute_script(script='g.v(0)')
        self.assertTrue(isinstance(n, client.Node))

    def test_gremlin_extension_reference_node_returns(self):
        # Assuming the GremlinPlugin installed
        ext = self.gdb.extensions.GremlinPlugin
        n = ext.execute_script(script='g.v(0)', returns=constants.NODE)
        self.assertTrue(isinstance(n, client.Node))

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

    def test_gremlin_extension_relationships_returns(self):
        # Assuming the GremlinPlugin installed
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        n3 = self.gdb.nodes.create()
        n1.relationships.create("related", n2)
        n1.relationships.create("related", n3)
        gremlin = self.gdb.extensions.GremlinPlugin.execute_script
        import options as clientDebug
        clientDebug.DEBUG = True
        rels = gremlin(script='g.v(%s).outE' % n1.id,
                       returns=constants.RELATIONSHIP)
        self.assertEqual(len(rels), 2)
        for rel in rels:
            self.assertTrue(isinstance(rel, client.Relationship))
        clientDebug.DEBUG = False

    def test_gremlin_extension_reference_raw_returns(self):
        # Assuming the GremlinPlugin installed
        ext = self.gdb.extensions.GremlinPlugin
        n = ext.execute_script(script='g.v(0)', returns=constants.RAW)
        self.assertTrue(isinstance(n, dict))


class TransactionsTestCase(ExtensionsTestCase):

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
        n1 = self.gdb.nodes.get(1)
        with self.gdb.transaction():
            n2 = self.gdb.nodes.get(1)
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
        with self.gdb.transaction(commit=False, using_globals=False) as tx1:
            with self.gdb.transaction(commit=False, using_globals=False) as tx2:
                n.delete("age", tx=tx1)
                n["name"] = tx2("Jonathan")
                n["place", tx2] = "Toronto"
        self.assertTrue("age" in n.properties)
        tx1.commit()
        self.assertTrue("age" not in n.properties)
        self.assertEqual(n["name"], "John")
        self.assertEqual(n["place"], "Houston")
        tx2.commit()
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
        import options as clientDebug
        clientDebug.DEBUG = True
        nodes = []
        with self.gdb.transaction(commit=False) as tx:
            for i in range(5):
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

    def test_transaction_create_relationship_functional_mixed2(self):
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

    def test_transaction_create_relationship_functional(self):
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
    # https://github.com/mhluongo/neo4j-rest-client/blob/master/neo4jrestclient/tests.py
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
            index.add('test1','test1', n1)
            index['test2']['test2'] = n1
        self.assertTrue(index['test1']['test1'][-1] == n1)
        self.assertTrue(index['test2']['test2'][-1] == n1)

    def test_transaction_index_add_rel_to_index(self):
        """
        Tests whether a relationship can be added to an index within a transaction.
        Does not assert transactionality.
        """
        #test nodes
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        r = n1.relationships.create('Knows', n2)
        index = self.gdb.relationships.indexes.create('index_rel')
        with self.gdb.transaction():
            index.add('test1','test1', r)
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
        index.add('test2','test2', n1)
        # Test getting nodes from index during transaction
        tx = self.gdb.transaction()
        index_hits = index['test2']['test2']
        tx.commit()
        self.assertTrue(n1 == index_hits[:][-1])

    def test_transaction_remove_node_from_index(self):
        index = self.gdb.nodes.indexes.create('index3')
        n = self.gdb.nodes.create()
        index.add('test3','test3', n)
        tx = self.gdb.transaction(using_globals=False)
        index.delete('test3', 'test3', n, tx=tx)
        # Assert transactional
        self.assertTrue(n in index['test3']['test3'])
        tx.commit()
        self.assertTrue(n not in index['test3']['test3'])

    def test_transaction_query_index_for_new_node(self):
        #test nodes created in transaction
        
        index = self.gdb.nodes.indexes.create('index4%s' \
                                              % datetime.now().microsecond)
        tx = self.gdb.transaction(using_globals=False)
        n4 = self.gdb.nodes.create(tx=tx)
        index.add('test3','test3', n4, tx=tx)
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
        index.add('test1','test1', n1)
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
            return node['test1'] == 'test1' and \
                   node['test2'] == 'test2'

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

#    def test_transaction_traversal(self):
#        nodes = [self.gdb.nodes.create() for i in xrange(10)]
#        # Chain them into a linked list
#        last = None
#        for n in nodes:
#            if last:
#                last.relationships.create("Knows", n)
#            last = n

#        with self.gdb.transaction():
#            tx_n = self.gdb.node()
#            last.relationships.create('Knows', tx_n)
#            types = [
#                client.All.Knows,
#            ]
#            stop = constants.STOP_AT_END_OF_GRAPH
#            traversal = nodes[0].traverse(types=types, stop=stop)

#        #a non-transactional traversal will be 1 node short
#        self.assertEqual(len(traversal), len(nodes))


class PickleTestCase(TransactionsTestCase):

    def test_node_pickle(self):
        n = self.gdb.nodes.create()
        p = pickle.dumps(n)
        self.assertEqual(n, pickle.loads(p))

    def test_relationship_pickle(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        r = n1.relationships.create("related", n2)
        p = pickle.dumps(r)
        self.assertEqual(r, pickle.loads(p))


class Neo4jPythonClientTestCase(PickleTestCase):
    pass

if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    suite = test_loader.loadTestsFromTestCase(Neo4jPythonClientTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
