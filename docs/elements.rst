Elements
========

Nodes
-----

Due to the syntax is fully compatible with neo4j.py_, the next lines only show
the commands added and its differences.

Creating a node::

  >>> n = gdb.nodes.create()
  
  # Equivalent to
  >>> n = gdb.node()

Specify properties for new node::

  >>> n = gdb.nodes.create(color="Red", width=16, height=32)
  
  # Or
  >>> n = gdb.node(color="Red", width=16, height=32)

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


Relationships
-------------

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


.. _neo4j.py: http://components.neo4j.org/neo4j.py/
.. _lucene-querybuilder: http://github.com/scholrly/lucene-querybuilder
