Neo4j Python REST Client
========================

:synopsis: Allows interact with Neo4j standalone REST server from Python.

The first objective of Neo4j Python REST Client is to make transparent for
Python programmers the use of a local database through neo4j.py_ or a remote
database thanks to Neo4j REST Server. So, the syntax of this API is fully
compatible with neo4j.py. However, a new syntax is introduced in order to
reach a more pythonic style.

The main file is named client.py, but you can rename with whatever you want.


Instantiation
-------------

The main class is *GraphDatabase*, exactly how in neo4j.py_::

  >>> from client import GraphDatabase
  
  >>> gdb = GraphDatabase("http://localhost:9999")

Two global options are available::

  client.CACHE = False # Default

If CACHE is 'True', a '.cache' directory is created and the future request to
the same URL will be taken from cache
And::

  client.DEBUG = False # Default

If DEBUG is 'True', 'httplib2' is set to debuglevel = 1.


Node, Relationships and Properties
----------------------------------

Due to the syntax is fully compatible with neo4j.py_, the next lines only show
the commands added and its differences.

Creating a node::

  >>> n = graphdb.node()
  
  # Equivalent to
  >>> n = graphdb.nodes.create()

Specify properties for new node::

  >>> n = graphdb.node(color="Red", widht=16, height=32)
  
  # Or
  >>> n = graphdb.nodes.create(color="Red", widht=16, height=32)

Accessing node by id::

  >>> n = graphdb.node[14]
  
  # Using the identifier or the URL is possible too
  >>> n = graphdb.nodes.get(14)

Accessing properties::

  >>> value = n['key'] # Get property value
  
  >>> n['key'] = value # Set property value
  
  >>> del n['key']     # Remove property value
  
  # Or the other way
  >>> value = n.get('key', 'default') # Support 'default' values
  
  >>> n.set('key', value)
  
  >>> n.delete('key')

Besides, a Node object has other attributes::

  >>> n.properties
  {}
  
  >>> n.properties = {'name': 'John'}
  {'name': 'John'}
  
  # The URL and the identifier assigned by Neo4j are added too
  >>> n.id
  14
  
  >>> n.url
  'http://localhost:9999/node/14'

Create relationship::

  >>> n1.Knows(n2)
  
  # Or
  >>> n1.relationships.create("Knows", n2) # Usefull when the name of
                                           # relationship is stored in a variable

Specify properties for new relationships::

  >>> n1.Knows(n2, since=123456789, introduced_at="Christmas party")
  
  # It's the same to
  >>> n1.relationships.create("Knows", n2, since=123456789,
                                           introduced_at="Christmas party")

The creation returns a Relationship object, which has properties, setter and
getters like a node::

  >>> rel = n1.relationships.create("Knows", n2, since=123456789)
  
  >>> rel.start
  <Neo4j Node: http://localhost:9999/node/14>
  
  >>> rel.end
  <Neo4j Node: http://localhost:9999/node/32>
  
  >>> rel.type
  'Knows'
  
  >>> rel.properties
  {'since': 123456789}

Others functions over 'relationships' attribute are possible. Like get all,
incoming or outgoing relationships (typed or not)::

  >>> rels = n1.relationships.all()
  [<Neo4j Relationship: http://localhost:9999/relationship/35843>,
   <Neo4j Relationship: http://localhost:9999/relationship/35840>,
   <Neo4j Relationship: http://localhost:9999/relationship/35841>,
   <Neo4j Relationship: http://localhost:9999/relationship/35842>,
   <Neo4j Relationship: http://localhost:9999/relationship/35847>,
   <Neo4j Relationship: http://localhost:9999/relationship/35846>,
   <Neo4j Relationship: http://localhost:9999/relationship/35845>,
   <Neo4j Relationship: http://localhost:9999/relationship/35844>,
   <Neo4j Relationship: http://localhost:9999/relationship/11>,
   <Neo4j Relationship: http://localhost:9999/relationship/10>,
   <Neo4j Relationship: http://localhost:9999/relationship/9>]
  
  >>> rels = n1.relationships.incoming(types=["Knows"])
  [<Neo4j Relationship: http://localhost:9999/relationship/35843>,
   <Neo4j Relationship: http://localhost:9999/relationship/35840>,
   <Neo4j Relationship: http://localhost:9999/relationship/11>,
   <Neo4j Relationship: http://localhost:9999/relationship/10>,
   <Neo4j Relationship: http://localhost:9999/relationship/9>]
  
  >>> rels = n1.relationships.outgoing(["Knows", "Loves"])
  [<Neo4j Relationship: http://localhost:9999/relationship/35842>,
   <Neo4j Relationship: http://localhost:9999/relationship/35847>]


Traversals
----------

The traversals framework is supported too with the same syntax of neo4j.py_,
but with some added issues.

Regular way::

  >>> n1.relationships.create("Knows", n2, since=1970)
  <Neo4j Relationship: http://localhost:9999/relationship/36009>
  
  >>> class TraversalClass(gdb.Traversal):
     ...:     types = [
     ...:         Undirected.Knows
     ...:     ]
     ...: 
  
  >>> [traversal for traversal in TraversalClass(n1)]
  [<Neo4j Node: http://localhost:9999/node/15880>]

Added way (more ''pythonic'')::

  >>> n1.relationships.create("Knows", n2, since=1970)
  <Neo4j Relationship: http://localhost:9999/relationship/36009>
  
  >>> n1.traverse(types=[client.Undirected.Knows])
  [<Neo4j Node: http://localhost:9999/node/15880>]


Transaction
-----------

Currently, the transaction support is not implemented in Neo4j REST server, so
the Python client is not able to provide it.


.. _neo4j.py: http://components.neo4j.org/neo4j.py/
