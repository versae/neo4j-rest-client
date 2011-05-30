Neo4j Python REST Client
========================

:synopsis: Allows interact with Neo4j standalone REST server from Python.

The first objective of Neo4j Python REST Client is to make transparent for
Python programmers the use of a local database through neo4j.py_ or a remote
database thanks to Neo4j REST Server. So, the syntax of this API is fully
compatible with neo4j.py. However, a new syntax is introduced in order to
reach a more pythonic style.


Installation
------------

Available throught Python Package Index::

  $ pip install neo4jrestclient

Or::

  $ easy_install neo4jrestclient


Getting started
---------------

The main class is *GraphDatabase*, exactly how in neo4j.py_::

  >>> from neo4jrestclient import GraphDatabase
  
  >>> gdb = GraphDatabase("http://localhost:7474/db/data/")

Two global options are available::

  neo4jrestclient.request.CACHE = False # Default

If CACHE is 'True', a '.cache' directory is created and the future request to
the same URL will be taken from cache
And::

  neo4jrestclient.request.DEBUG = False # Default

If DEBUG is 'True', 'httplib2' is set to debuglevel = 1.


Node, Relationships and Properties
----------------------------------

Due to the syntax is fully compatible with neo4j.py_, the next lines only show
the commands added and its differences.

Creating a node::

  >>> n = gdb.nodes.create()
  
  # Equivalent to
  >>> n = gdb.node()

Specify properties for new node::

  >>> n = gdb.nodes.create(color="Red", widht=16, height=32)
  
  # Or
  >>> n = gdb.node(color="Red", widht=16, height=32)

Accessing node by id::

  >>> n = gdb.node[14]
  
  # Using the identifier or the URL is possible too
  >>> n = gdb.nodes.get(14)

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
  'http://localhost:7474/db/data/node/14'

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
  <Neo4j Node: http://localhost:7474/db/data/node/14>
  
  >>> rel.end
  <Neo4j Node: http://localhost:7474/db/data/node/32>
  
  >>> rel.type
  'Knows'
  
  >>> rel.properties
  {'since': 123456789}

Or you can create the relationship using directly from GraphDatabse object::

  >>> rel = gdb.relationships.create(n1, "Hates", n2)
  
  >>> rel
  <Neo4j Relationship: http://localhost:7474/db/data/relationship/66>

  >>> rel.start
  <Neo4j Node: http://localhost:7474/db/data/node/14>
  
  >>> rel.end
  <Neo4j Node: http://localhost:7474/db/data/node/32>


Others functions over 'relationships' attribute are possible. Like get all,
incoming or outgoing relationships (typed or not)::

  >>> rels = n1.relationships.all()
  [<Neo4j Relationship: http://localhost:7474/db/data/relationship/35843>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/35840>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/35841>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/35842>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/35847>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/35846>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/35845>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/35844>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/11>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/10>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/9>]
  
  >>> rels = n1.relationships.incoming(types=["Knows"])
  [<Neo4j Relationship: http://localhost:7474/db/data/relationship/35843>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/35840>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/11>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/10>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/9>]
  
  >>> rels = n1.relationships.outgoing(["Knows", "Loves"])
  [<Neo4j Relationship: http://localhost:7474/db/data/relationship/35842>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/35847>]


Traversals
----------

The traversals framework is supported too with the same syntax of neo4j.py_,
but with some added issues.

Regular way::

  >>> n1.relationships.create("Knows", n2, since=1970)
  <Neo4j Relationship: http://localhost:7474/db/data/relationship/36009>
  
  >>> class TraversalClass(gdb.Traversal):
     ...:     types = [
     ...:         Undirected.Knows
     ...:     ]
     ...: 
  
  >>> [traversal for traversal in TraversalClass(n1)]
  [<Neo4j Node: http://localhost:7474/db/data/node/15880>]

Added way (more ''pythonic'')::

  >>> n1.relationships.create("Knows", n2, since=1970)
  <Neo4j Relationship: http://localhost:7474/db/data/relationship/36009>
  
  >>> n1.traverse(types=[neo4jrestclient.Undirected.Knows])
  [<Neo4j Node: http://localhost:7474/db/data/node/15880>]


Indexes
-------

Due to the original neo4j.py_ currently doesn't provide support for the new
index component, for nodes and for relationships, the syntax for indexing is
not compliant, quite different and, hopefully, more intuitive::

  >>> i1 =  gdb.nodes.indexes.create("index1")
  
  >>> i2 =  gdb.nodes.indexes.create("index2", type="fulltext", provider="lucene")
  
  >>> gdb.nodes.indexes
  {u'index2': <Neo4j Index: http://localhost:7474/db/data/index/node/index2>,
   u'index1': <Neo4j Index: http://localhost:7474/db/data/index/node/index1>}
  
  >>> gdb.nodes.indexes.get("index1")
  <Neo4j Index: http://localhost:7474/db/data/index/node/index1>

You can query and add elements to the index like a 3-dimensional array or
using the convenience methods::

  >>> i1["key"]["value"]
  []
  
  >>> i1.get("key")["value"]
  []
  
  >>> i1.get("key", "value")
  []
  
  >>> i1["key"]["value"] = n1
  
  >>> i1.add("key", "value", n2)
  
  >>> i1["key"]["value"]
  [<Neo4j Node: http://localhost:7474/db/data/node/1>,
   <Neo4j Node: http://localhost:7474/db/data/node/2>]

The advanced query is also supported if the index is created with the type
'fulltext' ('lucene' is the default provider)::

  >>> n1 = gdb.nodes.create(name="John Doe", place="Texas")
  
  >>> n2 = gdb.nodes.create(name="Michael Donald", place="Tijuana")
  
  >>> i1 = gdb.nodes.indexes.create(name="do", type="fulltext")
  
  >>> i1["surnames"]["doe"] = n1
  
  >>> i1["surnames"]["donald"] = n2
  
  >>> i1.query("surnames", "do*")
  [<Neo4j Node: http://localhost:7474/db/data/node/295>,
   <Neo4j Node: http://localhost:7474/db/data/node/296>]

Deleting nodes from an index::

  >>> i1.delete("key", "values", n1)
  
  >>> i1.delete("key", None, n2)

And in order to work with indexes of relationships the instructions are the
same::

  >>> i3 =  gdb.relationships.indexes.create("index3")



Extensions
----------

The server plugins are supported as extensions of GraphDatabase, Node or
Relationship objects::

  >>> gdb.extensions
  {u'GetAll': <Neo4j ExtensionModule: [u'get_all_nodes', u'getAllRelationships']>}
  >>> gdb.extensions.GetAll
  <Neo4j ExtensionModule: [u'get_all_nodes', u'getAllRelationships']>
  
  >>> gdb.extensions.GetAll.getAllRelationships()
  
  [<Neo4j Relationship: http://localhost:7474/db/data/relationship/0>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/1>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/2>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/3>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/4>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/5>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/6>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/7>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/8>]

An example using extensions over nodes::

  >>> n1 = gdb.nodes.get(0)
  
  >>> n1.extensions
  {u'DepthTwo': <Neo4j ExtensionModule: [u'nodesOnDepthTwo', u'relationshipsOnDepthTwo', u'pathsOnDepthTwo']>, u'ShortestPath': <Neo4j ExtensionModule: [u'shortestPath']>}
  
  >>> n2 = gdb.nodes.get(1)
  
  >>> n1.relationships.create("Kwnos", n2)
  <Neo4j Relationship: http://localhost:7474/db/data/relationship/36>
  
  >>> n1.extensions.ShortestPath
  <Neo4j ExtensionModule: [u'shortestPath']>
  
  >>> n1.extensions.ShortestPath.shortestPath.parameters
  
  [{u'description': u'The node to find the shortest path to.',
    u'name': u'target',
    u'optional': False,
    u'type': u'node'},
   {u'description': u'The relationship types to follow when searching for the shortest path(s). Order is insignificant, if omitted all types are followed.',
    u'name': u'types',
    u'optional': True,
    u'type': u'strings'},
   {u'description': u'The maximum path length to search for, default value (if omitted) is 4.',
    u'name': u'depth',
    u'optional': True,
    u'type': u'integer'}]



Transaction
-----------

Currently, the transaction support is not implemented in Neo4j REST server, so
the Python client is not able to provide it.


.. _neo4j.py: http://components.neo4j.org/neo4j.py/
