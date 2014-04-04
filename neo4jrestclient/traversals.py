# -*- coding: utf-8 -*-
# From https://gist.github.com/1865786 by @aventurella
# http://docs.neo4j.org/chunked/snapshot/rest-api-traverse.html
#       #rest-api-traversal-returning-nodes-below-a-certain-depth
from neo4jrestclient import constants
from neo4jrestclient.iterable import Iterable
from neo4jrestclient.request import Request
from neo4jrestclient.exceptions import NotFoundError, StatusException
from neo4jrestclient.utils import string_types


class GraphTraversal(object):
    types = None
    order = None
    stop = None
    returnable = None
    uniqueness = None
    paginated = None
    page_size = None
    time_out = None
    returns = None
    is_returnable = None
    isReturnable = None
    is_stop_node = None
    isStopNode = None

    def __init__(self, start_node=None):
        self.start_node = start_node
        is_returnable = self.is_returnable or self.isReturnable
        is_stop_node = self.is_stop_node or self.isStopNode
        results = self.start_node.traverse(types=self.types,
                                           order=self.order,
                                           stop=self.stop,
                                           returnable=self.returnable,
                                           uniqueness=self.uniqueness,
                                           is_stop_node=is_stop_node,
                                           is_returnable=is_returnable,
                                           paginated=self.paginated,
                                           page_size=self.page_size,
                                           time_out=self.time_out,
                                           returns=self.returns)
        self._items = results
        self._index = len(results)

    def __iter__(self):
        return self

    def __next__(self):
        if self._index == 0:
            raise StopIteration
        self._index = self._index - 1
        return self._items[self._index]

    def next(self):
        return self.__next__()


class Order(object):
    BREADTH_FIRST = constants.BREADTH_FIRST
    DEPTH_FIRST = constants.DEPTH_FIRST


class Uniqueness(object):
    NODE_GLOBAL = constants.NODE_GLOBAL
    NONE = constants.NONE
    RELATIONSHIP_GLOBAL = constants.RELATIONSHIP_GLOBAL
    NODE_PATH = constants.NODE_PATH
    RELATIONSHIP_PATH = constants.RELATIONSHIP_PATH


class RelationshipDirection(object):
    ANY = constants.RELATIONSHIPS_ALL
    ALL = constants.RELATIONSHIPS_ALL
    INCOMING = constants.RELATIONSHIPS_IN
    OUTGOING = constants.RELATIONSHIPS_OUT


class Filters(object):
    """Filters answer the question (return true/false)
    Evaluation.INCLUDE_AND_CONTINUE
    Evaluation.EXCLUDE_AND_CONTINUE
    """
    ALL = {"language": "builtin", "name": constants.RETURN_ALL_NODES}
    ALL_BUT_START_NODE = {
        "language": "builtin",
        "name": constants.RETURN_ALL_BUT_START_NODE,
    }


class PruneEvaluators(object):
    """PruneEvaluators answer the question (return true/false)
    Evaluation.INCLUDE_AND_PRUNE
    Evaluation.EXCLUDE_AND_PRUNE
    """
    pass


class Traverser(object):
    NODE = constants.NODE
    RELATIONSHIP = constants.RELATIONSHIP
    PATH = constants.PATH
    FULLPATH = constants.FULLPATH

    def __init__(self, start_node, data, auth=None, cypher=None):
        self._auth = auth or {}
        self._cypher = cypher
        self._data = data
        self._endpoint = start_node._dic["traverse"]
        self._cache = {}

    def request(self, return_type):
        try:
            return self._cache[return_type]
        except KeyError:
            url = self._endpoint.replace("{returnType}", return_type)
            response = Request(**self._auth).post(url, data=self._data)
            if response.status_code == 200:
                results_list = response.json()
                self._cache[return_type] = results_list
                return results_list
            elif response.status_code == 404:
                raise NotFoundError(response.status_code,
                                    "Node or relationship not found")
            raise StatusException(response.status_code, "Invalid data sent")

    @property
    def nodes(self):
        from neo4jrestclient.client import Node
        results = self.request(Traverser.NODE)
        return Iterable(Node, results, "self", cypher=self._cypher)

    @property
    def relationships(self):
        from neo4jrestclient.client import Relationship
        results = self.request(Traverser.RELATIONSHIP)
        return Iterable(Relationship, results, "self")

    @property
    def fullpaths(self):
        raise NotImplementedError()

    def __iter__(self):
        from neo4jrestclient.client import Path
        results = self.request(Traverser.PATH)
        return Iterable(Path, results, auth=self._auth)


class TraversalDescription(object):
    """https://github.com/neo4j/community/blob/master/kernel/src/main
              /java/org/neo4j/graphdb/traversal/TraversalDescription.java"""

    def __init__(self, auth=None, cypher=None):
        self._auth = auth or {}
        self._cypher = cypher
        self._data = {}
        self.uniqueness(Uniqueness.NODE_GLOBAL)
        # self.max_depth(1)

    def uniqueness(self, value):
        self._data["uniqueness"] = value
        return self

    def filter(self, value):
        try:
            value["language"]
            self._data["return_filter"] = value
        except KeyError:
            self._data["return_filter"] = {
                "language": "javascript",
                "body": value,
            }
        return self

    def prune(self, value, language="javascript"):
        try:
            value["language"]
            self._data["prune_evaluator"] = value
        except KeyError:
            self._data["prune_evaluator"] = {"language": language,
                                             "body": value}

    def order(self, value):
        self._data["order"] = value
        return self

    def depthFirst(self, value=None):
        self.order(Order.DEPTH_FIRST)
        return self

    def breadthFirst(self, value=None):
        self.order(Order.BREADTH_FIRST)
        return self

    def relationships(self, name, direction=RelationshipDirection.ALL):
        self._data["relationships"] = []
        if (not isinstance(name, string_types) and hasattr(name, "type")
                and hasattr(name, "direction")):
            direction = name.direction
            name = name.type
        self.relationships_append(name, direction)
        self.relationships = self.relationships_append
        return self

    def relationships_append(self, name, direction=RelationshipDirection.ALL):
        if (not isinstance(name, string_types) and hasattr(name, "type")
                and hasattr(name, "direction")):
            direction = name.direction
            name = name.type
        self._data["relationships"].append({
            "direction": direction,
            "type": name,
        })
        return self

    def max_depth(self, value):
        self._data["max_depth"] = value

    def traverse(self, start_node):
        try:
            self._data['prune_evaluator']
            del self._data["max_depth"]
        except KeyError:
            pass
        return Traverser(start_node, self._data, auth=self._auth,
                         cypher=self._cypher)


class Traversal(object):

    def __init__(self, start_node):
        self._description = Traversal.description()
        self._start_node = start_node

    @property
    def description(self):
        return self._description

    def __iter__(self):
        return self._description.traverse(self._start_node)
