Indices
=======

The original neo4j.py_ currently did not provide support for the new
index component. However, the current syntax for indexing is now  compliant
with the python-embedded_ API, and hopefully more intuitive::

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
`fulltext` (`lucene` is the default provider) by entering a Lucene query::

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


.. _neo4j.py: http://components.neo4j.org/neo4j.py/
.. _lucene-querybuilder: http://github.com/scholrly/lucene-querybuilder
.. _python-embedded: http://docs.neo4j.org/chunked/snapshot/python-embedded.html
