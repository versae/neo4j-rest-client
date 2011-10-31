# -*- coding: utf-8 -*-
__author__ = "Javier de la Rosa"
__credits__ = [
    "Javier de la Rosa",
    "Diego Muñoz Escalante, https://github.com/escalant3",
    "Yashh, https://github.com/yashh",
    "timClicks, https://github.com/timClicks",
    "Mark Henderson, https://github.com/emehrkay",
    "Johan Lundberg, https://github.com/johanlundberg",
    "Mark Ng, https://github.com/markng",
    "kesavkolla, https://github.com/kesavkolla",
    "Andy Denmark, https://github.com/denmark",
]
__license__ = "GPL 3"
__version__ = "1.5.0"
__email__ = "versae@gmail.com"
__url__ = "https://github.com/versae/neo4j-rest-client"
__description__ = """Object-oriented Python library to interact with """ \
                  """Neo4j standalone REST server"""
__status__ = "Development"
# Order
BREADTH_FIRST = "breadth_first"
DEPTH_FIRST = "depth_first"
# Relationships
RELATIONSHIPS_ALL = "all"
RELATIONSHIPS_IN = "in"
RELATIONSHIPS_OUT = "out"
# Return
RETURN_ALL_NODES = "all"
RETURN_ALL_BUT_START_NODE = "all_but_start_node"
# Stop
STOP_AT_DEPTH_ONE = 1
STOP_AT_END_OF_GRAPH = "none"
# Uniqueness
NONE = "none"
NODE_GLOBAL = "node_global"
NODE_PATH = "node_path"
NODE_RECENT = "node recent"  # Deprecated
RELATIONSHIP_GLOBAL = "relationship_global"
RELATIONSHIP_PATH = "relationship_path"
RELATIONSHIP_RECENT = "relationship recent"  # Deprecated
# Returns
NODE = "node"
RELATIONSHIP = "relationship"
PATH = "path"
FULLPATH = "fullpath"
POSITION = "position"
# Indexes
INDEX_EXACT = "exact"
INDEX_FULLTEXT = "fulltext"
# Transactions
TX_GET = "GET"
TX_PUT = "PUT"
TX_POST = "POST"
TX_DELETE = "DELETE"
