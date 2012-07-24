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

Or even if you want to use the development branch::

  $ pip install git+https://github.com/versae/neo4j-rest-client.git


Getting started
---------------

The main class is *GraphDatabase*, exactly how in neo4j.py_::

  >>> from neo4jrestclient.client import GraphDatabase
  
  >>> gdb = GraphDatabase("http://localhost:7474/db/data/")

For providing authentication like is needed in services like Heroku_, you
should add the proper parameters::

  >>> url = "http://<instance>.hosted.neo4j.org:7000/db/data/"
  
  >>> gdb = GraphDatabase(url, username="username", password="password")


Options
-------

There some global options available::
If CACHE is 'True', a '.cache' directory is created and the future request to
the same URL will be taken from cache::

  neo4jrestclient.options.CACHE = False # Default

You can also use your own custom cache, (e.g LocMemCache from django)::

    neo4jrestclient.options.CACHE_STORE = LocMemCache()

If DEBUG is 'True', 'httplib2' is set to debuglevel = 1::

  neo4jrestclient.options.DEBUG = False # Default

And SMART_ERRORS, set to 'False' by default. In case of 'True', the standard
HTTP errors will be replaced by more pythonic errors (i.e. 'KeyError' instead
of 'NotFoundError' in some cases)::

  neo4jrestclient.options.SMART_ERRORS = False # Default


.. _neo4j.py: http://components.neo4j.org/neo4j.py/
.. _lucene-querybuilder: http://github.com/scholrly/lucene-querybuilder
.. _Heroku: http://devcenter.heroku.com/articles/neo4j
