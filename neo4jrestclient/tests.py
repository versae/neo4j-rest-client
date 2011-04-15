import client
import request
import unittest


class NodesTestCase(unittest.TestCase):

    def setUp(self):
        self.url = "http://localhost:7474/db/data/"
        self.gdb = client.GraphDatabase(self.url)

    def test_connection_cache(self):
        import request as clientCache
        clientCache.CACHE = True
        gdb = client.GraphDatabase(self.url)
        clientCache.CACHE = False
        self.assertEqual(gdb.url, self.url)

    def test_connection_debug(self):
        import request as clientDebug
        clientDebug.DEBUG = True
        gdb = client.GraphDatabase(self.url)
        clientDebug.DEBUG = False
        self.assertEqual(gdb.url, self.url)

    def test_connection_cache_debug(self):
        import request as clientCacheDebug
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


class IndexesTestCase(RelationshipsTestCase):

    def test_create_index_for_nodes(self):
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        index = self.gdb.nodes.indexes.create(name="doe")
        index["surnames"]["d"] = n1
        self.failUnless(n1 in index["surnames"]["d"])

    def test_create_index_for_relationships(self):
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        n2 = self.gdb.nodes.create(name="Michael Doe", place="Tijuana")
        r1 = self.gdb.relationships.create(n1, "Hates", n2)
        index = self.gdb.relationships.indexes.create(name="brothers")
        index["feeling"]["hate"] = r1
        self.failUnless(r1 in index["feeling"]["hate"])

    def test_delete_node_from_index(self):
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        index = self.gdb.nodes.indexes.create(name="doe")
        index["surnames"]["d"] = n1
        index.delete("surnames", "d", n1)
        self.failUnless(n1 not in index["surnames"]["d"])

    def test_delete_relationship_from_index(self):
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        n2 = self.gdb.nodes.create(name="Michael Doe", place="Tijuana")
        r1 = self.gdb.relationships.create(n1, "Hates", n2)
        index = self.gdb.relationships.indexes.create(name="brothers")
        index["feeling"]["hate"] = r1
        index.delete("feeling", "hate", r1)
        self.failUnless(r1 not in index["feeling"]["hate"])

    def test_query_index(self):
        n1 = self.gdb.nodes.create(name="John Doe", place="Texas")
        n2 = self.gdb.nodes.create(name="Michael Donald", place="Tijuana")
        index = self.gdb.nodes.indexes.create(name="do", type="fulltext")
        index["surnames"]["doe"] = n1
        index["surnames"]["donald"] = n2
        results = index.query("surnames", "do*")
        self.failUnless(n1 in results and n2 in results)


class TraversalsTestCase(IndexesTestCase):

    def test_create_traversal(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        n1.relationships.create("Knows", n2, since=1970)
        types = [
            client.Undirected.Knows,
        ]
        traversal = n1.traverse(types=types)
        self.failUnless(len(traversal) > 0)

    def test_create_traversal_class(self):
        n1 = self.gdb.nodes.create()
        n2 = self.gdb.nodes.create()
        n1.relationships.create("Knows", n2, since=1970)

        class TraversalClass(self.gdb.Traversal):

            types = [
                client.Undirected.Knows,
            ]

        results = []
        for result in TraversalClass(n1):
            results.append(result)
        self.failUnless(len(results) > 0)


class ExtensionsTestCase(TraversalsTestCase):

    def test_get_graph_extensions(self):
        fail = False
        try:
            self.gdb.extensions
        except:
            fail = True
        self.failUnless(not fail)

    def test_get_node_extensions(self):
        fail = False
        n1 = self.gdb.nodes.create()
        try:
            n1.extensions
        except:
            fail = True
        self.failUnless(not fail)


class Neo4jPythonClientTestCase(ExtensionsTestCase):
    pass

if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    suite = test_loader.loadTestsFromTestCase(Neo4jPythonClientTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
