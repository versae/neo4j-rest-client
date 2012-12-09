Neo4j Python REST Client
========================

:synopsis: Object-oriented Python library to interact with Neo4j standalone REST server.

The first objective of Neo4j Python REST Client is to make transparent for
Python programmers the use of a local database through python-embedded_ or a
remote database thanks to Neo4j REST Server. So, the syntax of this API is
fully compatible with python-embedded. However, a new syntax is introduced in
order to reach a more pythonic style.


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

The main class is *GraphDatabase*, exactly how in python-embedded_:

  >>> from neo4jrestclient.client import GraphDatabase
  
  >>> gdb = GraphDatabase("http://localhost:7474/db/data/")

For providing authentication like is needed in services like Heroku_, you
should add the proper parameters:

  >>> url = "http://<instance>.hosted.neo4j.org:7000/db/data/"
  
  >>> gdb = GraphDatabase(url, username="username", password="password")

Or even using certificates:

  >>> gdb = GraphDatabase(url, username="username", password="password",
     ...: cert_file='path/to/file.cert', key_file='path/to/file.key')

Due to a limitation of `httplib2`, both files must be in PEM_ format.


Options
-------

There some global options available::
If CACHE is `True`, a `.cache` directory is created and the future request to
the same URL will be taken from cache::

  neo4jrestclient.options.CACHE = False # Default

You can also use your own custom cache, (e.g LocMemCache from django)::

  neo4jrestclient.options.CACHE_STORE = LocMemCache()

If DEBUG is `True`, `httplib2` is set to debuglevel = 1::

  neo4jrestclient.options.DEBUG = False # Default

And `SMART_ERRORS`, set to 'False' by default. In case of `True`, the standard
HTTP errors will be replaced by more pythonic errors (i.e. `KeyError` instead
of `NotFoundError` in some cases)::

  neo4jrestclient.options.SMART_ERRORS = False # Default


.. _python-embedded: http://docs.neo4j.org/chunked/snapshot/python-embedded.html
.. _lucene-querybuilder: http://github.com/scholrly/lucene-querybuilder
.. _`read the docs`: http://readthedocs.org/docs/neo4j-rest-client/en/latest/
.. _Documentation: http://readthedocs.org/docs/neo4j-rest-client/en/latest/
.. _Installation: https://neo4j-rest-client.readthedocs.org/en/latest/info.html#installation
.. _`Getting started`: https://neo4j-rest-client.readthedocs.org/en/latest/info.html#getting-started
.. _Heroku: http://devcenter.heroku.com/articles/neo4j
.. _PEM: http://en.wikipedia.org/wiki/X.509#Certificate_filename_extensions
