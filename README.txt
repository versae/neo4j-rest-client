Neo4j Python REST Client
========================

:synopsis: Object-oriented Python library to interact with Neo4j standalone REST server.

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

Due to the syntax is fully compatible with neo4j.py_, the next lines only show
the commands added and its differences.

Creating a node::

  >>> n = gdb.nodes.create()
  
  # Equivalent to
  >>> n = gdb.node()

Specify properties for new node::

  >>> n = gdb.nodes.create(color="Red", widht=16, height=32)

Accessing properties::

  >>> value = n['key'] # Get property value
  
  >>> n['key'] = value # Set property value

Create relationship::

  >>> n1.relationships.create("Knows", n2) # Usefull when the name of
                                           # relationship is stored in a variable

Specify properties for new relationships::

  >>> n1.Knows(n2, since=123456789, introduced_at="Christmas party")


Documentation
-------------

For an extended and lates version of the documentation, please, visit the
docs_ site:: http://readthedocs.org/docs/neo4j-rest-client/en/latest/



.. _neo4j.py: http://components.neo4j.org/neo4j.py/
.. _lucene-querybuilder: http://github.com/scholrly/lucene-querybuilder
.. _docs: http://readthedocs.org/docs/neo4j-rest-client/en/latest/
