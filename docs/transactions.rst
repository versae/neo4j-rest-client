Transactions
============

Currently, the transaction support is not complete in this client, although
a work in progress is being carried out, and hopefully the capacity to
handle objects created in the same transaction will be done.

Basic usage for deletion::

  >>> n = gdb.nodes.create()
  
  >>> n["age"] = 25
  
  >>> n["place"] = "Houston"
  
  >>> n.properties
  {'age': 25, 'place': 'Houston'}
  
  >>> with gdb.transaction():
     ....:         n.delete("age")
     ....: 
  
  >>> n.properties
  {u'place': u'Houston'}


When a transaction is performed, the values of the properties of the objects
are updated automatically. However, this can be controled by hand adding a
parameter in the transaction::

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


Apart from update or deletion of properties, there is also creation. In this
case, the object just created is returned through a 'TransactionOperationProxy'
object, which is automatically converted in the proper object when the
transaction ends. This is the second part of the commit process and a parameter
in the transaction can be added to avoid the commit::

  >>> n1 = gdb.nodes.create()
  
  >>> n2 = gdb.nodes.create()
  
  >>> with gdb.transaction(commit=False) as tx:
     .....:         for i in range(1, 11):
     .....:             n1.relationships.create("relation_%s" % i, n2)
     .....: 
  
  >>> len(n1.relationships)
  0

The 'commit' method of the transaction object returns 'True' if there's no any
fail. Otherwose, it returns 'None'::

  >>> tx.commit()
  True
  
  >>> len(n1.relationships)
  10


In order to avoid the need of setting the transaction variable, 'neo4jrestclient'
uses a global variable to handle all the transactions. The name of the variable
can be changed using de options::

  >>> client.options.TX_NAME = "_tx"  # Default value


And this behaviour can be disabled adding the right param in the transaction:
'using_globals'. Even is possible (although not very recommendable) to handle
different transactions in the same time and control when they are commited.
There are many ways to set the transaction of a intruction (operation)::

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
