Traversals
==========

The traversals framework is supported too with the same syntax of neo4j.py_,
but with some added issues.

Regular way::

  >>> n1.relationships.create("Knows", n2, since=1970)
  <Neo4j Relationship: http://localhost:7474/db/data/relationship/36009>
  
  >>> class TraversalClass(gdb.Traversal):
     ...:     types = [
     ...:         client.All.Knows,
     ...:     ]
     ...: 
  
  >>> [traversal for traversal in TraversalClass(n1)]
  [<Neo4j Node: http://localhost:7474/db/data/node/15880>]

Added way (the types of relationships are 'All', 'Incoming', 'Outgoing')::

  >>> n1.relationships.create("Knows", n2, since=1970)
  <Neo4j Relationship: http://localhost:7474/db/data/relationship/36009>
  
  >>> n1.traverse(types=[client.All.Knows])[:]
  [<Neo4j Node: http://localhost:7474/db/data/node/15880>]


For getting a paginated traversal is only needed one of the next parameters: 
'paginated' to enable the pagination, 'page_size' to set the size of returned
page, and 'time_out' to establish the lease time that the server will wait for.
After set any of this parameters, the traversal call will return an iterable 
object of traversals called 'PaginatedTraversal'::

  >>> pages = n1.traverse(types=[client.All.Knows], stop=stop, page_size=5)
  
  >>> pages
  <PaginatedTraversal object at 0x25a5150>
  
  >>> [n for n in [traversal for traversal in pages]]
  [<Neo4j Node: http://localhost:7474/db/data/node/15880>]


.. _neo4j.py: http://components.neo4j.org/neo4j.py/
.. _lucene-querybuilder: http://github.com/scholrly/lucene-querybuilder
