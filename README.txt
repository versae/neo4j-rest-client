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

  >>> from neo4jrestclient.client import GraphDatabase
  
  >>> gdb = GraphDatabase("http://localhost:7474/db/data/")

Options
-------

There some global options available::
If CACHE is 'True', a '.cache' directory is created and the future request to
the same URL will be taken from cache::

  neo4jrestclient.options.CACHE = False # Default

If DEBUG is 'True', 'httplib2' is set to debuglevel = 1::

  neo4jrestclient.options.DEBUG = False # Default

And SMART_ERRORS, set to 'False' by default. In case of 'True', the standard
HTTP errors will be replaced by more pythonic errors (i.e. 'KeyError' instead
of 'NotFoundError' in some cases)::

  neo4jrestclient.options.SMART_ERRORS = False # Default


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
  <Neo4j Iterable: Relationship>

In order improve the performance of the 'neo4jrestclient', minimizing the 
number of HTTP requests that are made, all the functions that should return
list of objects like Nodes, Relationships, Paths or Positions, they actually
return an Iterable object that extends the Python 'list' type::

  >>> rels = n1.relationships.all()[:]
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
  
  >>> rels = n1.relationships.incoming(types=["Knows"])[:]
  [<Neo4j Relationship: http://localhost:7474/db/data/relationship/35843>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/35840>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/11>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/10>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/9>]
  
  >>> rels = n1.relationships.outgoing(["Knows", "Loves"])[:]
  [<Neo4j Relationship: http://localhost:7474/db/data/relationship/35842>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/35847>]

There's a shortcut to access to the list of all relationships::

  >>> rels = n1.relationships.all()[2]
  <Neo4j Relationship: http://localhost:7474/db/data/relationship/47>

It's the same to::

  >>> rels = n1.relationships[2]
  <Neo4j Relationship: http://localhost:7474/db/data/relationship/47>

And::

  >>> rels = n1.relationships.get(2)
  <Neo4j Relationship: http://localhost:7474/db/data/relationship/47>



Traversals
----------

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
  
  >>> i1["key"]["value"][:]
  [<Neo4j Node: http://localhost:7474/db/data/node/1>,
   <Neo4j Node: http://localhost:7474/db/data/node/2>]

Advanced queries are also supported if the index is created with the type
'fulltext' ('lucene' is the default provider) by entering a Lucene query::

  >>> n1 = gdb.nodes.create(name="John Doe", place="Texas")
  
  >>> n2 = gdb.nodes.create(name="Michael Donald", place="Tijuana")
  
  >>> i1 = gdb.nodes.indexes.create(name="do", type="fulltext")
  
  >>> i1["surnames"]["doe"] = n1

  >>> i1["places"]["Texas"] = n1
  
  >>> i1["surnames"]["donald"] = n2

  >>> i1["places"]["Tijuana"] = n2
  
  >>> i1.query("surnames", "do*")[:]
  [<Neo4j Node: http://localhost:7474/db/data/node/295>,
   <Neo4j Node: http://localhost:7474/db/data/node/296>]

...or by using the DSL described by lucene-querybuilder_ to support boolean
operations and nested queries::

  >>> i1.query(Q('surnames','do*') & Q('places','Tijuana'))[:]
  [<Neo4j Node: http://localhost:7474/db/data/node/295>]

Deleting nodes from an index::

  >>> i1.delete("key", "values", n1)
  
  >>> i1.delete("key", None, n2)

And in order to work with indexes of relationships the instructions are the
same::

  >>> i3 =  gdb.relationships.indexes.create("index3")

For deleting an index just call 'delete' with no arguments::

  >>> i3.delete()


Extensions
----------

The server plugins are supported as extensions of GraphDatabase, Node or
Relationship objects::

  >>> gdb.extensions
  {u'GetAll': <Neo4j ExtensionModule: [u'get_all_nodes',
                                       u'getAllRelationships']>}
  >>> gdb.extensions.GetAll
  <Neo4j ExtensionModule: [u'get_all_nodes', u'getAllRelationships']>
  
  >>> gdb.extensions.GetAll.getAllRelationships()[:]
  
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
  {u'DepthTwo': <Neo4j ExtensionModule: [u'nodesOnDepthTwo',
                                         u'relationshipsOnDepthTwo',
                                         u'pathsOnDepthTwo']>,
   u'ShortestPath': <Neo4j ExtensionModule: [u'shortestPath']>}
  
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
   {u'description': u'The relationship types to follow when searching for ...',
    u'name': u'types',
    u'optional': True,
    u'type': u'strings'},
   {u'description': u'The maximum path length to search for, ...',
    u'name': u'depth',
    u'optional': True,
    u'type': u'integer'}]



Transactions
------------

Currently, the transaction support is not complete in this client, although
a work in progress is being carried out, and hopefully the capacity to
handle objects created in the same transaction will be done.

Basic usage for deletion::

  >>> n = gdb.nodes.create()
  
  >>> n["age"] = 25
  
  >>> n["place"] = "Houston"
  
  >>> n.properties
  {'age': 25, 'place': 'Houston'}
  
  >>> with gdb.transaction():
     ....:         n.delete("age")
     ....: 
  
  >>> n.properties
  {u'place': u'Houston'}


When a transaction is performed, the values of the properties of the objects
are updated automatically. However, this can be controled by hand adding a
parameter in the transaction::

  >>> n = gdb.nodes.create()
  
  >>> n["age"] = 25
  
  >>> with gdb.transaction(update=False):
     ....:         n.delete("age")
     ....: 
  
  >>> n.properties
  {'age': 25}
  
  >>> n.update()
  
  >>> n.properties
  {}


Apart from update or deletion of properties, there is also creation. In this
case, the object just created is returned through a 'TransactionOperationProxy'
object, which is automatically converted in the proper object when the
transaction ends. This is the second part of the commit process and a parameter
in the transaction can be added to avoid the commit::

  >>> n1 = gdb.nodes.create()
  
  >>> n2 = gdb.nodes.create()
  
  >>> with gdb.transaction(commit=False) as tx:
     .....:         for i in range(1, 11):
     .....:             n1.relationships.create("relation_%s" % i, n2)
     .....: 
  
  >>> len(n1.relationships)
  0

The 'commit' method of the transaction object returns 'True' if there's no any
fail. Otherwose, it returns 'None'::

  >>> tx.commit()
  True
  
  >>> len(n1.relationships)
  10


In order to avoid the need of setting the transaction variable, 'neo4jrestclient'
uses a global variable to handle all the transactions. The name of the variable
can be changed using de options::

  >>> client.options.TX_NAME = "_tx"  # Default value


And this behaviour can be disabled adding the right param in the transaction:
'using_globals'. Even is possible (although not very recommendable) to handle
different transactions in the same time and control when they are commited.
There are many ways to set the transaction of a intruction (operation)::

  >>> n = gdb.nodes.create()
  
  >>> n["age"] = 25
  
  >>> n["name"] = "John"
  
  >>> n["place"] = "Houston"
  
  >>> with gdb.transaction(commit=False, using_globals=False) as tx1, \
     ....:      gdb.transaction(commit=False, using_globals=False) as tx2:
     ....:         n.delete("age", tx=tx1)
     ....:     n["name"] = tx2("Jonathan")
     ....:     n["place", tx2] = "Toronto"
     ....: 
  
  >>> "age" in n.properties
  True
  
  >>> tx1.commit()
  True
  
  >>> "age" in n.properties
  False
  
  >>> n["name"] == "John"
  True
  
  >>> n["place"] == "Houston"
  True
  
  >>> tx2.commit()
  True
  
  >>> n["name"] == "John"
  False
  
  >>> n["place"] == "Houston"
  False



.. _neo4j.py: http://components.neo4j.org/neo4j.py/
.. _lucene-querybuilder: http://github.com/scholrly/lucene-querybuilder
