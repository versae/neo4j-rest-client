import client
import unittest


class TestNodes(unittest.TestCase):

    def setUp(self):
        self.gdb = client.GraphDatabase("http://localhost:9999")

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

    def test_create_node_properties(self):
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
        self.assertEqual(n1.get("name"), n1.get("name"))

    def test_set_node_properties(self):
        n1 = self.gdb.node(name="John Doe", profession="Hacker")
        n1.properties = {"name": "Jimmy Doe"}
        n2 = self.gdb.node[n1.id]
        self.assertEqual(n1.properties, n2.properties)

    def test_del_node_property_dictionary(self):
        n1 = self.gdb.node(name="John Doe", profession="Hacker")
        del n1["name"]
        self.assertEqual(n1.get("name", None), None)

    def test_del_node_property(self):
        n1 = self.gdb.nodes.create(name="John Doe", profession="Hacker")
        n1.delete("name")
        self.assertEqual(n1.get("name", None), None)

    def test_del_node_properties(self):
        n1 = self.gdb.node(name="John Doe", profession="Hacker")
        del n1.properties
        self.assertEqual(n1.properties, {})

    def test_del_node(self):
        n1 = self.gdb.nodes.create(name="John Doe", profession="Hacker")
        identifier = n1.id
        n1.delete()
        try:
            self.gdb.nodes.get(identifier)
            self.assertTrue(False)
        except client.NotFoundError, client.StatusException:
            self.assertTrue(True)


class TestRelationships(unittest.TestCase):

    def setUp(self):
        self.gdb = client.GraphDatabase("http://localhost:9999")

    def test_create_node(self):
        n = self.gdb.nodes.create()
        self.assertEqual(n.properties, {})


if __name__ == '__main__':
    nodes_suite = unittest.TestLoader().loadTestsFromTestCase(TestNodes)
    unittest.TextTestRunner(verbosity=2).run(nodes_suite)
    relationships_suite = unittest.TestLoader().loadTestsFromTestCase(TestRelationships)
    unittest.TextTestRunner(verbosity=2).run(relationships_suite)
