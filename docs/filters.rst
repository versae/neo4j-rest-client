Filters
=======

On top of Queries feature, there are some filtering helpers for nodes,
relationships and both indices. First thing you need is to define `Q` objects:

  >>> from neo4jrestclient.query import Q
  
  >>> Q("name", istartswith="william")

Once a lookup is defined, you may call the `filter` method over all
the nodes or the relationships:

  >>> gdb.nodes.filter(lookup)
  [<Neo4j Node: http://localhost:7474/db/data/node/14>]

Or just a list of elements identifiers, `Node`'s or `Relationship`'s:

  >>> nodes = []
  
  >>> for i in range(2):
     ...: nodes.append(gdb.nodes.create(name="William %s" % i))
  
  >>> lookup = Q("name", istartswith="william")
  
  >>> williams = gdb.nodes.filter(lookup, start=nodes)


Lookups
-------

The syntax for lookups is very similar to the one used in Django_, but does
include other options:

  Q(property_name, lookup=match)

The next list shows all the current lookups supported:

* `exact`, performs exact string comparation.
* `iexact`, performs exact string comparation, case insesitive.
* `contains`, checks if the property is contained in the string passed.
* `icontains`, as `contains` but case insesitive.
* `startswith`, checks if the property starts with the string passed.
* `istartswith`, as `startswith` but case insesitive.
* `endswith`, checks if the property ends with the string passed.
* `iendswith`, as `endswith` but case insesitive.
* `regex`, performs regular expression matching agains the string passed.
* `iregex`, as `regex` but case insesitive.
* `gt`, check if the property is greater than the value passed.
* `gte`, check if the property is greater than or equal to the value passed.
* `lt`, check if the property is lower than the value passed.
* `lte`, check if the property is lower than or equal to the value passed.
* `in`, , check if the property is in a list of elements passed.
* `inrange`,`an alias for `in`.
* `isnull`, checks if the property is null, passing `True`, or not, passing `False`.
* `eq`, performs equal comparations.
* `equals`, an alias `eq`.
* `neq`, performs not equal comparations.
* `notequals`, an alias `neq`.

Also, in order to be compliant with Cypher syntax, you can add a `nullable`
parameter to set if the lookup must be don using `!` or `?`. By default, all
lookups are nullable.

  >>> lookup = Q("name", istartswith="william", nullable=True)
  
  >>> lookup
  n.`name`! =~ (?i)william.*
  
  >>> lookup = Q("name", istartswith="william", nullable=False)
  
  >>> lookup
  n.`name`? =~ (?i)william.*
  
  >>> lookup = Q("name", istartswith="william", nullable=None)
  
  >>> lookup
  n.`name` =~ (?i)william.*


There is support for complex lookups as well:

  >>> lookups = (Q("name", exact="James")
     ...:  & (Q("surname", startswith="Smith") & ~Q("surname", endswith="e")))
  ( n.`name`! = James AND ( n.`surname`! =~ Smith.* AND NOT ( n.`surname`! =~ .*1 ) ) )



Ordering
--------

There is an feature to set the order by which the elements will be returned,
using the Cypher option `order by`. The syntax is a tuple: the first element is
the property name to order by, the second one the type of ordering, `constants.ASC`
for ascending, and `constants.DESC` for descending. A set of orderings can be used:

  >>> gdb.nodes.filter(lookup).order_by("code", constants.DESC)


Indices
-------

Indices also implement the `filter` method, so you can use an index as a start,
or just invoke the method to filter the elements:

  >>> old_loves = gdb.relationships.filter(lookup, start=index)
  
  >>> old_loves = gdb.relationships.filter(lookup, start=index["since"])

So, the next would be the same:

  >>> old_loves = index.filter(lookup)
  
  >>> old_loves = index.filter(lookup, key="since")
  
  >>> old_loves = index["since"].filter(lookup)

However, it is not possible yet to pass a value for the index using the common
dictionary syntax. Instead, you may use the `value` parameter:

  >>> old_loves = index.filter(lookup, key="since", value=1990)


Slicing
-------

In addition, all filters implement lazy slicing, so the query is not run until
the results are going to be retrieved. However, there is not still support for
transactions:

  >>> lookup = Q("name", istartswith="william")
  
  >>> results = gdb.nodes.filter(lookup)  # Not query executed yet
  
  >>> len(restuls)  # Here the query is executed
  12

If the elements of the filter have been already retrieved from the server, the
slicing is then run against the local version. If not, the `slice` is transformed
into `limit` and `skip` options before doing the request.

  >>> results = gdb.nodes.filter(lookup)  # Not query executed yet
  
  >>> restuls[1:2]  # The Cypher query is limited using limit and skip
  [<Neo4j Node: http://localhost:7474/db/data/node/14>]
  
  >>> len(results)  # The Cypher query is sent again to the server
  12

.. _Django: https://docs.djangoproject.com/en/dev/topics/db/queries/#complex-lookups-with-q-objects
