Queries
=======

Since the Cypher plugin is not a plugin anymore, neo4j-rest-client_ is able to
run queries and returns the results properly formatted:

  >>> q = """start n=node(*) return n"""

  >>> result = gdb.query(q=q)

Returned types
--------------

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

Query statistics
----------------

Extra information about the execution of a each query is stored in the
property `stats`.

  >>> query = "MATCH (n)--() RETURN n LIMIT 5"
  >>> results = gdb.query(query, data_contents=True)
  >>> results.stats
  {u'constraints_added': 0,
   u'constraints_removed': 0,
   u'contains_updates': False,
   u'indexes_added': 0,
   u'indexes_removed': 0,
   u'labels_added': 0,
   u'labels_removed': 0,
   u'nodes_created': 0,
   u'nodes_deleted': 0,
   u'properties_set': 0,
   u'relationship_deleted': 0,
   u'relationships_created': 0}


Graph and row data contents
---------------------------

The Neo4j REST API is able to provide the results of a query in other two
formats that might be useful when redering. To enable this option (which is the
default only when running inside a IPython Notebook), you might pass an extra
parameter to the query, `data_contents`. If set to `True`, it will populate the
properties `.rows` as a list of rows, and `.graph` as a graph representation of
the result.

  >>> query = "MATCH (n)--() RETURN n LIMIT 5"
  >>> results = gdb.query(query, data_contents=True)
  >>> results.rows
  [[{u'name': u'M\xedchael Doe', u'place': u'T\xedjuana'}],
   [{u'name': u'J\xf3hn Doe', u'place': u'Texa\u015b'}],
   [{u'name': u'Rose 0'}],
   [{u'name': u'William 0'}],
   [{u'name': u'Rose 1'}]]
  >>> results.graph
    [{u'nodes': [{u'id': u'3',
      u'labels': [],
      u'properties': {u'name': u'M\xedchael Doe', u'place': u'T\xedjuana'}}],
    u'relationships': []},
   {u'nodes': [{u'id': u'2',
      u'labels': [],
      u'properties': {u'name': u'J\xf3hn Doe', u'place': u'Texa\u015b'}}],
    u'relationships': []},
   {u'nodes': [{u'id': u'45',
      u'labels': [],
      u'properties': {u'name': u'Rose 0'}}],
    u'relationships': []},
   {u'nodes': [{u'id': u'44',
      u'labels': [],
      u'properties': {u'name': u'William 0'}}],
    u'relationships': []},
   {u'nodes': [{u'id': u'47',
      u'labels': [],
      u'properties': {u'name': u'Rose 1'}}],
    u'relationships': []}]

If only one of the represenations is needed, `data_contents` can be either
`constants.DATA_ROWS` or `constants.DATA_GRAPH`.



.. _neo4j-rest-client: http://pypi.python.org/pypi/neo4jrestclient/
.. _`collection function`: http://docs.neo4j.org/chunked/stable/query-functions-collection.html
.. _`collection functions`: http://docs.neo4j.org/chunked/stable/query-functions-collection.html
