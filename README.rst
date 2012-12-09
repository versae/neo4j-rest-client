Neo4j Python REST Client
========================

:synopsis: Object-oriented Python library to interact with Neo4j standalone REST server.

The first objective of Neo4j Python REST Client is to make transparent for
Python programmers the use of a local database through python-embedded_ or a
remote database thanks to Neo4j REST Server. So, the syntax of this API is
fully compatible with python-embedded. However, a new syntax is introduced in
order to reach a more pythonic style.


Installation_
-------------

Available throught Python Package Index::

  $ pip install neo4jrestclient

Or::

  $ easy_install neo4jrestclient


`Getting started`_
------------------

The main class is *GraphDatabase*, exactly how in python-embedded_::

  >>> from neo4jrestclient.client import GraphDatabase

  >>> gdb = GraphDatabase("http://localhost:7474/db/data/")

Due to the syntax is fully compatible with python-embedded_, the next lines only show
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


Documentation_
--------------

For the extended and latest version of the documentation, please, visit the
`read the docs`_ site



.. _python-embedded: http://docs.neo4j.org/chunked/snapshot/python-embedded.html
.. _lucene-querybuilder: http://github.com/scholrly/lucene-querybuilder
.. _`read the docs`: http://readthedocs.org/docs/neo4j-rest-client/en/latest/
.. _Documentation: http://readthedocs.org/docs/neo4j-rest-client/en/latest/
.. _Installation: https://neo4j-rest-client.readthedocs.org/en/latest/info.html#installation
.. _`Getting started`: https://neo4j-rest-client.readthedocs.org/en/latest/info.html#getting-started
