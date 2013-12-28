Options
=======

There some global options available in neo4j-rest-client that change
internal behaviours.

``CACHE``
---------

If ``CACHE`` is ``True``, a ``.cache`` directory is created and the future
requests to the same URL will be taken from cache:

  >>> neo4jrestclient.options.CACHE = False  # Default

The location and name of the ``.cache`` can be changed by modifying the option
``CACHE_STORE``.

  >>> neo4jrestclient.options.CACHE_STORE = "/path/to/cache"

The neo4j-rest-client's cache is implemented using CacheControl_ for
requests_, so you shouldn't have any problem using your own custom cache
(e.g ``LocMemCache`` from Django)::

  >>> neo4jrestclient.options.CACHE_STORE = LocMemCache()


``DEBUG``
---------

If ``DEBUG`` is ``True``, ``httplib.HTTPConnection.debuglevel`` is set to ``1``,
and requests_ enables its logger::

  >>> neo4jrestclient.options.DEBUG = False   # Default


``SMART_DATES``
---------------

There is experimental support for ``date``, ``time``, and ``datetime`` objects
since Neo4j does not support natively (yet) those data types. What
neo4j-rest-client does is to use a specific format to store them as strings,
and convert them from Python objects to string (and viceversa) when needed.

To enable this feature you can set ``SMART_DATES`` to ``True``:

  >>> neo4jrestclient.options.SMART_DATES = False  # Default

The format in which ``date``, ``time``, and ``datetime`` objects are stored can
be changed by modifying the next values:

  >>> neo4jrestclient.options.DATE_FORMAT = "%Y-%m-%d"
  >>> neo4jrestclient.options.TIME_FORMAT = "%H:%M:%S.%f"
  >>> neo4jrestclient.options.DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


``SMART_ERRORS``
----------------

And ``SMART_ERRORS``, set to ``False`` by default. In case of ``True``, the standard
HTTP errors will be replaced by more pythonic errors (i.e. ``KeyError`` instead
of ``NotFoundError`` in some cases):

  >>> neo4jrestclient.options.SMART_ERRORS = False  # Default


``TX_NAME``
-----------
It is extremely weird to have the need to change this option, but in case that
you need a different name for the memory variable that will store in progress
transactions (aka batch operations), you can do that with ``TX_NAME``:

  >>> neo4jrestclient.options.TX_NAME = "_tx"  # Default


.. _python-embedded: http://docs.neo4j.org/chunked/snapshot/python-embedded.html
.. _lucene-querybuilder: http://github.com/scholrly/lucene-querybuilder
.. _`read the docs`: http://readthedocs.org/docs/neo4j-rest-client/en/latest/
.. _Documentation: http://readthedocs.org/docs/neo4j-rest-client/en/latest/
.. _Installation: https://neo4j-rest-client.readthedocs.org/en/latest/info.html#installation
.. _`Getting started`: https://neo4j-rest-client.readthedocs.org/en/latest/info.html#getting-started
.. _Heroku: http://devcenter.heroku.com/articles/neo4j
.. _requests: http://docs.python-requests.org/en/latest/
.. _CacheControl: http://cachecontrol.readthedocs.org/en/latest/
.. _PEM: http://en.wikipedia.org/wiki/X.509#Certificate_filename_extensions
