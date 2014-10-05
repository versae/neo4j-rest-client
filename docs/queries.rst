Queries
=======

Since the Cypher plugin is not a plugin anymore, neo4j-rest-client_ is able to
run queries and returns the results properly formatted:

  >>> q = """start n=node(*) return n"""

  >>> result = gdb.query(q=q)

This way to run a query will return the results as RAW, i.e., in the same way
the REST interface get them. However, you can always use a ``returns`` parameter
in order to perform custom castings:

  >>> q = """start n=node(*) match n-[r]-() return n, n.name, r"""

  >>> results = gdb.query(q, returns=(client.Node, unicode, client.Relationship))

  >>> results[0]
  [<Neo4j Node: http://localhost:7474/db/data/node/14>,
  u'John Doe',
  <Neo4j Relationship: http://localhost:7474/db/data/relationship/47>]

Or pass a custom function:

  >>> is_john_doe = lambda x: x == "John Doe"

  >>> results = gdb.query(q, returns=(client.Node, is_john_doe, client.Relationship))
  >>> results[0]
  [<Neo4j Node: http://localhost:7474/db/data/node/14>,
  True,
  <Neo4j Relationship: http://localhost:7474/db/data/relationship/47>]

If the length of the elements is greater than the casting functions passed through
the ``returns`` parameter, the `RAW` will be used instead of raising an exception.

Sometimes query results include lists, as it happens when using ``COLLECT`` or other
`collection functions`_, ``neo4j-rest-client`` is able to handle these cases by passing
lists or tuples in the `results` list. Usually these lists contain items of the
same type, so passing only one casting function is enough, as all the items are
treated the same way.

  >>> a = gdb.nodes.create()
  >>> [a.relationships.create("rels", gdb.nodes.create()) for x in range(3)]
  [<Neo4j Relationship: http://localhost:7474/db/data/relationship/43>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/44>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/45>]
  >>> q = """match (a)--(b) with a, collect(b) as bs return a, bs limit 1"""

  >>> gdb.query(q, returns=(client.Node, [client.Node, ]))[0]
  [<Neo4j Node: http://localhost:7474/db/data/node/31>,
   [<Neo4j Node: http://localhost:7474/db/data/node/29>,
    <Neo4j Node: http://localhost:7474/db/data/node/28>,
    <Neo4j Node: http://localhost:7474/db/data/node/30>]]

  >>> gdb.query(q, returns=(client.Node, (client.Node, )))[0]
  [<Neo4j Node: http://localhost:7474/db/data/node/31>,
   (<Neo4j Node: http://localhost:7474/db/data/node/29>,
    <Neo4j Node: http://localhost:7474/db/data/node/28>,
    <Neo4j Node: http://localhost:7474/db/data/node/30>)]

  >>> gdb.query(query, returns=[client.Node, client.Iterable(client.Node)])[0]
  [<Neo4j Node: http://localhost:7474/db/data/node/3672>,
   <listiterator at 0x7f6958c6ff50>]


However, if you know in advance how many elements are going to be returned as
the result of a `collection function`_, you can always customize the casting functions:

  >>> gdb.query(q, returns=(client.Node, (client.Node, lambda x: x["data"], client.Node )))[0]
  [<Neo4j Node: http://localhost:7474/db/data/node/31>,
   (<Neo4j Node: http://localhost:7474/db/data/node/29>,
    {u'tag': u'tag1'},
    <Neo4j Node: http://localhost:7474/db/data/node/30>)]

.. _neo4j-rest-client: http://pypi.python.org/pypi/neo4jrestclient/
.. _`collection function`: http://docs.neo4j.org/chunked/stable/query-functions-collection.html
.. _`collection functions`: http://docs.neo4j.org/chunked/stable/query-functions-collection.html
