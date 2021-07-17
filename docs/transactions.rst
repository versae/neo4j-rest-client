Transactions and Batch
======================

Transactions in Cypher
----------------------

Neo4j provides, since its version 2.0.0, a transactional endpoint for Cypher
queries. That feature is wrapped in 'neo4jrestclient' in the ``gdb.transaction()``
method. But for backwards compatibility issues (there were *transactions* before),
you need to add an extra parameter ``for_query=True`` in order to enable it.

Object-based
++++++++++++

The easiest way to use a transaction is by creating a ``tx`` object:

  >>> tx = gdb.transaction(for_query=True)


While the transaction is alive, a property ``finished`` is set to ``False``. The
property ``expires`` has a string with the date sent by the server.

  >>> tx.finished
  False
  >>> tx.expires
  "Sun, 08 Dec 2013 15:05:52 +0000"


Now, regular Cypher queries can be added to the transaction and executed or
in server:

  >>> tx.append("CREATE (a) RETURN a", returns=client.Node)
  >>> tx.append("CREATE (b) RETURN b", params={}  )
  >>> results = tx.execute()
  >>> len(results) == 2
  True

Both methods, ``execute()`` and `commit()`, return a ``QuerySequence`` with
the results of the queries sent to the server. You can now perform any check
on the returned objects, and if there is something wrong, rollback the
transaction and restore the previous state of the database.

  >>> tx.rollback()
  >>> len(results)
  0

Or you can commit and get the remaining results returned by server:

  >>> tx.append("MERGE (c:Person {name:'Carol'})")
  >>> tx.append("MERGE (d:Person {name:'Dave'})")
  >>> results = tx.commit()
  >>> len(results) == 2
  True

After ``commit()`` or ``rollback()``, the transaction is destroyed and no queries
can be appended.


Inside a ``with`` statement
+++++++++++++++++++++++++++

For your convinience and wider control of the logic of your application,
transactions can be written inside a ``with`` statement. This way, you don't need
a ``tx`` object and can use the regular syntax for queries. Each independent
query is executed in the transaction, so you have the returned values and can
operate with them:

  >>> q = "start n=node(*) match n-[r:`{rel}`]-() return n, n.name, r, r.since"
  >>> params = {"rel": "Knows"}
  >>> returns = (client.Node, str, client.Relationship)
  >>> with self.gdb.transaction(for_query=True) as tx:
  ...     self.gdb.query("MERGE (c:Person {name:'Carol'})")
  ...     results = self.gdb.query(q, params=params, returns=returns)
  ...     node = results[0][0]
  ...     if node["name"] == "Carol":
  ...         tx.rollback()



Batch-based Transactions
------------------------

The transaction support for regular opertations, like CRUD and indexing on
nodes and relationships, is based on the REST endpoint
for batch operations, therefore there is some limitations because **it is not**
a real transaction. When a batch of operations is sent to the server, Neo4j
executes it in a transaction, but there is no option to rollback and recover
a previous status of the database. In this sense, batch-emulated transactions
for operations on creation, edition and deletion of elements are useful, but
you won't be able to perform checks on the elements modified until the batch
is sent to the server and the transaction is committed.


Deletion
++++++++

Basic usage for deletion:

  >>> n = gdb.nodes.create()
  >>> n["age"] = 25
  >>> n["place"] = "Houston"
  >>> n.properties
  {'age': 25, 'place': 'Houston'}
  >>> with gdb.transaction():
  ...     n.delete("age")
  ...
  >>> n.properties
  {u'place': u'Houston'}


Creation
++++++++

Apart from update or deletion of properties, there is also creation. In this
case, the object just created is returned through a ``TransactionOperationProxy``
object, which is automatically converted in the proper object when the
transaction ends. This is the second part of the commit process and a parameter
in the transaction, ``commit`` can be added to avoid the commit:

  >>> n1 = gdb.nodes.create()
  >>> n2 = gdb.nodes.create()
  >>> with gdb.transaction() as tx:
     .....:         for i in range(1, 11):
     .....:             n1.relationships.create("relation_%s" % i, n2)
     .....:
  >>> len(n1.relationships) != 0
  True


Auto-update and auto-commit
+++++++++++++++++++++++++++

When a transaction is performed, the values of the properties of the objects
are updated automatically. However, this can be controled by hand adding a
parameter in the transaction:

  >>> n = gdb.nodes.create()
  >>> n["age"] = 25
  >>> with gdb.transaction(update=False):
     ....:         n.delete("age")
     ....:
  >>> n.properties
  {'age': 25}
  >>> n.update()
  >>> n.properties
  {}


You can also set ``commit=False`` and commit manually after the ``with`` block
is over:

  >>> with gdb.transaction(commit=False) as tx:
     ....:         n.delete("age")
     ....:
  >>> n.properties
  {'age': 25}
  >>> tx.commit()
  >>> n.properties
  {}


The ``commit`` method of the transaction object returns `True` if there's no any
fail. Otherwise, it returns 'None':

  >>> tx.commit()
  True
  >>> len(n1.relationships)
  10


Globals and nesting
+++++++++++++++++++

In order to avoid the need of setting the transaction variable, 'neo4jrestclient'
uses a global variable to handle all the transactions. The name of the variable
can be changed using de options:

  >>> client.options.TX_NAME = "_tx"  # Default value


And this behaviour can be disabled adding the right param in the transaction:
``using_globals``. Even is possible (although not very recommendable) to handle
different transactions in the same time and control when they are committed.
There are many ways to set the transaction of a intruction (operation):

  >>> n = gdb.nodes.create()
  >>> n["age"] = 25
  >>> n["name"] = "John"
  >>> n["place"] = "Houston"
  >>> with gdb.transaction(commit=False, using_globals=False) as tx1, \
     ....:      gdb.transaction(commit=False, using_globals=False) as tx2:
     ....:         n.delete("age", tx=tx1)
     ....:     n["name"] = tx2("Jonathan")
     ....:     n["place", tx2] = "Toronto"
     ....:

  >>> "age" in n.properties
  True

  >>> tx1.commit()
  True
  >>> "age" in n.properties
  False
  >>> n["name"] == "John"
  True
  >>> n["place"] == "Houston"
  True

  >>> tx2.commit()
  True
  >>> n["name"] == "John"
  False
  >>> n["place"] == "Houston"
  False



.. _neo4j.py: http://components.neo4j.org/neo4j.py/
.. _lucene-querybuilder: http://github.com/scholrly/lucene-querybuilder
