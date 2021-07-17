neo4j-rest-client's documentation
=================================

:synopsis: Object-oriented Python library to interact with Neo4j standalone REST server.

The main goal of neo4j-rest-client was to enable Python programmers
already using Neo4j locally through python-embedded_, to use the Neo4j REST
server. So the syntax of neo4j-rest-client's API is fully compatible with
python-embedded. However, a new syntax is introduced in order to reach a more
pythonic style and to enrich the API with the new features the Neo4j team
introduces.


Installation
------------

Available through Python Package Index::

  $ pip install neo4jrestclient

Or the old way::

  $ easy_install neo4jrestclient

You can also install the development branch::

  $ pip install git+https://github.com/versae/neo4j-rest-client.git


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

Authentication
^^^^^^^^^^^^^^
Authentication-based services like Heroku_ are also supported by passing extra
parameters:

  >>> url = "http://<instance>.hosted.neo4j.org:7000/db/data/"

  >>> gdb = GraphDatabase(url, username="username", password="password")

And when using certificates (both files must be in PEM_ format):

  >>> gdb = GraphDatabase(url, username="username", password="password",
                          cert_file='path/to/file.cert',
                          key_file='path/to/file.key')
