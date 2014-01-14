Labels
======

Labels are `tags` that you can associate a node to. A node can have more than one
label and a label can `have` more than one node.


Add and remove labels to/from a node
------------------------------------

For example, we can crete a couple of nodes:

  >>> alice = gdb.nodes.create(name="Alice", age=30)

  >>> bob = gdb.nodes.create(name="Bob", age=30)

And then put the label ``Person`` to both of them:

  >>> alice.labels.add("Person")
  >>> bob.labels.add("Person")

You can also add more than one label at the time, or replace all the labels of
a node:

  >>> alice.labels.add(["Person", "Woman"])
  >>> bob.labels = ["Person", "Man", "Woman"]

And remove labels in the same way:

  >>> bob.labels.remove("Woman")

Although using ``labels`` from a ``GraphDatabase`` is usually easier:

  >>> people = gdb.labels.create("Person")

  >>> people.add(alice, bob)

The call for ``gdb.labels.create`` **does not** actually create the label until
the first node is added.

We can also check if a node already has a specific label:

  >>> "Animal" in bob.labels
  False


List, get and filter
--------------------

One common use case for labels is to list all the nodes that are under the same
label. The most basic way to do it is by using the ``.all()`` method once we
assign a label to a variable:

  >>> person = gdb.labels.get("Person")
  >>> person.all()

Or get those nodes that has a certain pair property name and value:

  >>> person.get(age=25)

Can list and filter nodes according to the labels they are associated
to by using the ``Q`` objects provided by neo4j-rest-client:

  >>> from neo4jrestclient.query import Q
  >>> people.filter(gdb.Q("age", "gte", 30))
