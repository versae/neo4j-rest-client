.. neo4j-rest-client documentation master file, created by
   sphinx-quickstart on Mon Feb 27 11:54:51 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

neo4j-rest-client's documentation
=================================

:synopsis: Object-oriented Python library to interact with Neo4j standalone REST server.

The main goal of neo4j-rest-client was to enable Python programmers
already using Neo4j locally through python-embedded_, to use the Neo4j REST
server. So the syntax of neo4j-rest-client's API is fully compatible with
python-embedded. However, a new syntax is introduced in order to reach a more
pythonic style and to enrich the API with the new features the Neo4j team
introduces.


Getting started
---------------

The main class is ``GraphDatabase``, exactly how in python-embedded_:

  >>> from neo4jrestclient.client import GraphDatabase

  >>> gdb = GraphDatabase("http://localhost:7474/db/data/")

If ``/db/data/`` is not added, neo4j-rest-client will do an extra request in
order to know the endpoint for data.

And now we are ready to create nodes and relationships:

  >>> alice = gdb.nodes.create(name="Alice", age=30)

  >>> bob = gdb.nodes.create(name="Bob", age=30)

  >>> alice.relationships.create("Knows", bob, since=1980)

Although using ``labels`` is usually easier:

  >>> people = gdb.labels.create("Person")

  >>> people.add(alice, bob)

  >>> carl = people.create(name="Carl", age=25)

Now we can list and filter nodes according to the labels they are associated
to:

  >>> people.filter(Q("age", "gte", 30))


Installation
------------

Available through Python Package Index::

  $ pip install neo4jrestclient




.. _python-embedded: http://docs.neo4j.org/chunked/snapshot/python-embedded.html
.. _lucene-querybuilder: http://github.com/scholrly/lucene-querybuilder
.. _`read the docs`: http://readthedocs.org/docs/neo4j-rest-client/en/latest/
.. _Documentation: http://readthedocs.org/docs/neo4j-rest-client/en/latest/
.. _Installation: https://neo4j-rest-client.readthedocs.org/en/latest/info.html#installation
.. _`Getting started`: https://neo4j-rest-client.readthedocs.org/en/latest/info.html#getting-started
.. _Heroku: http://devcenter.heroku.com/articles/neo4j
.. _PEM: http://en.wikipedia.org/wiki/X.509#Certificate_filename_extensions


Contents:

.. toctree::
   :maxdepth: 2

   info
   elements
   labels
   indices
   queries
   filters
   traversals
   extensions
   transactions
   options
   changes

