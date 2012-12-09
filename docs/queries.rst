Queries
=======

Since the Cypher plugin is not a plugin anymore, neo4j-rest-client_ is able to
run queries and returns the results properly formatted:

  >>> q = """start n=node(*) return n"""
  
  >>> result = gdb.query(q=q)

This way to run a query will return the results as RAW, i.e., in the same way
the REST interface get them. However, you can always use a `returns` parameter
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

If the lenght of the elements is greater than the casting functions pass through
the `returns` parameter, the `RAW` will be used instead of raising an exception.


.. _neo4j-rest-client: http://pypi.python.org/pypi/neo4jrestclient/
