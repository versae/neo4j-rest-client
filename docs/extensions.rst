Extensions
==========

The server plugins are supported as extensions of GraphDatabase, Node or
Relationship objects::

  >>> gdb.extensions
  {u'GetAll': <Neo4j ExtensionModule: [u'get_all_nodes',
                                       u'getAllRelationships']>}
  >>> gdb.extensions.GetAll
  <Neo4j ExtensionModule: [u'get_all_nodes', u'getAllRelationships']>
  
  >>> gdb.extensions.GetAll.getAllRelationships()[:]
  
  [<Neo4j Relationship: http://localhost:7474/db/data/relationship/0>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/1>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/2>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/3>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/4>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/5>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/6>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/7>,
   <Neo4j Relationship: http://localhost:7474/db/data/relationship/8>]

An example using extensions over nodes::

  >>> n1 = gdb.nodes.get(0)
  
  >>> n1.extensions
  {u'DepthTwo': <Neo4j ExtensionModule: [u'nodesOnDepthTwo',
                                         u'relationshipsOnDepthTwo',
                                         u'pathsOnDepthTwo']>,
   u'ShortestPath': <Neo4j ExtensionModule: [u'shortestPath']>}
  
  >>> n2 = gdb.nodes.get(1)
  
  >>> n1.relationships.create("Kwnos", n2)
  <Neo4j Relationship: http://localhost:7474/db/data/relationship/36>
  
  >>> n1.extensions.ShortestPath
  <Neo4j ExtensionModule: [u'shortestPath']>
  
  >>> n1.extensions.ShortestPath.shortestPath.parameters
  
  [{u'description': u'The node to find the shortest path to.',
    u'name': u'target',
    u'optional': False,
    u'type': u'node'},
   {u'description': u'The relationship types to follow when searching for ...',
    u'name': u'types',
    u'optional': True,
    u'type': u'strings'},
   {u'description': u'The maximum path length to search for, ...',
    u'name': u'depth',
    u'optional': True,
    u'type': u'integer'}]


.. _neo4j.py: http://components.neo4j.org/neo4j.py/
.. _lucene-querybuilder: http://github.com/scholrly/lucene-querybuilder
