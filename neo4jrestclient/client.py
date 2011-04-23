# -*- coding: utf-8 -*-
import json
import urllib

from constants import (BREADTH_FIRST, DEPTH_FIRST,
                       STOP_AT_END_OF_GRAPH,
                       NODE_GLOBAL, NODE_PATH, NODE_RECENT,
                       RELATIONSHIP_GLOBAL, RELATIONSHIP_PATH,
                       RELATIONSHIP_RECENT,
                       NODE, RELATIONSHIP, PATH, POSITION,
                       INDEX_FULLTEXT)
from request import Request, NotFoundError, StatusException


class StopAtDepth(object):
    """
    Only traverse to a certain depth.
    """

    def __init__(self, depth):
        self.depth = depth

    def __get__(self):
        return self.depth


class MetaTraversal(type):
    """
    Metaclass for adding default attributes to Traversal class.
    """

    def __new__(cls, name, bases, dic):
        for attr in ["types", "order", "stop", "returnable", "uniqueness",
                     "returns"]:
            dic[attr] = dic.get(attr, None)
        dic["is_returnable"] = dic.get("is_returnable",
                                       dic.get("isReturnable", None))
        dic["is_stop_node"] = dic.get("is_stop_node",
                                      dic.get("isStopNode", None))
        return type.__new__(cls, name, bases, dic)


class GraphDatabase(object):
    """
    Main class for connection to Ne4j standalone REST server.
    """

    def __init__(self, url):
        self.url = None
        if url.endswith("/"):
            self.url = url
        else:
            self.url = "%s/" % url
        response, content = Request().get(url)
        if response.status == 200:
            response_json = json.loads(content)
            self._relationship_index = response_json['relationship_index']
            self._node = response_json['node']
            self._node_index = response_json['node_index']
            self._reference_node = response_json['reference_node']
            self._extensions_info = response_json['extensions_info']
            self._extensions = response_json['extensions']
            self.extensions = ExtensionsProxy(self._extensions)
            self.nodes = NodesProxy(self._node, self._reference_node,
                                    self._node_index)
            # Backward compatibility. The current style is more pythonic
            self.node = self.nodes
            # HACK: Neo4j doesn't provide the URLs to access to relationships
            url_parts = self._node.rpartition("node")
            self._relationship = "%s%s%s" % (url_parts[0], RELATIONSHIP,
                                             url_parts[2])
            self.relationships = RelationshipsProxy(self._relationship,
                                                    self._relationship_index)
            self.Traversal = self._get_traversal_class()
        else:
            raise NotFoundError(response.status, "Unable get root")

    def _get_reference_node(self):
        return Node(self._reference_node)
    reference_node = property(_get_reference_node)

    def traverse(self, *args, **kwargs):
        return self.reference_node.traverse(*args, **kwargs)

    def _get_traversal_class(self):
        cls = self

        class Traversal(object):
            __metaclass__ = MetaTraversal

            def __init__(self, start_node=None):
                if start_node and isinstance(start_node, Node):
                    self.start_node = start_node
                else:
                    self.start_node = cls.reference_node
                is_returnable = self.is_returnable
                is_stop_node = self.is_stop_node
                results = self.start_node.traverse(types=self.types,
                                                   order=self.order,
                                                   stop=self.stop,
                                                   returnable=self.returnable,
                                                   uniqueness=self.uniqueness,
                                                   is_stop_node=is_stop_node,
                                                   is_returnable=is_returnable,
                                                   returns=self.returns)
                self._items = results
                self._index = len(results)

            def __iter__(self):
                return self

            def next(self):
                if self._index == 0:
                    raise StopIteration
                self._index = self._index - 1
                return self._items[self._index]

        return Traversal


class Base(object):
    """
    Base class.
    """

    def __init__(self, url, create=False, data={}):
        self._dic = {}
        self.url = None
        if url.endswith("/"):
            url = url[:-1]
        if create:
            response, content = Request().post(url, data=data)
            if response.status == 201:
                self._dic.update(data.copy())
                self.url = response.get("location")
            else:
                raise NotFoundError(response.status, "Invalid data sent")
        if not self.url:
            self.url = url
        response, content = Request().get(self.url)
        if response.status == 200:
            self._dic.update(json.loads(content).copy())
            self._extensions = self._dic.get('extensions', {})
            if self._extensions:
                self.extensions = ExtensionsProxy(self._extensions)
        else:
            raise NotFoundError(response.status, "Unable get object")

    def delete(self, key=None):
        if key:
            self.__delitem__(key)
            return
        response, content = Request().delete(self.url)
        if response.status == 204:
            del self
        elif response.status == 404:
            raise NotFoundError(response.status, "Node or property not found")
        else:
            raise StatusException(response.status, "Node could not be "\
                                                   "deleted (still has " \
                                                   "relationships?)")

    def __getitem__(self, key):
        property_url = self._dic["property"].replace("{key}", key)
        response, content = Request().get(property_url)
        if response.status == 200:
            self._dic["data"][key] = json.loads(content)
        else:
            raise NotFoundError(response.status, "Node or propery not found")
        return self._dic["data"][key]

    def get(self, key, *args):
        if args:
            default = args[0]
            try:
                return self.__getitem__(key)
            except (KeyError, NotFoundError, StatusException):
                return default
        else:
            return self.__getitem__(key)

    def __contains__(self, obj):
        return obj in self._dic["data"]

    def __setitem__(self, key, value):
        property_url = self._dic["property"].replace("{key}", key)
        response, content = Request().put(property_url, data=value)
        if response.status == 204:
            self._dic["data"].update({key: value})
        elif response.status == 404:
            raise NotFoundError(response.status, "Node or property not found")
        else:
            raise StatusException(response.status, "Invalid data sent")

    def set(self, key, value):
        self.__setitem__(key, value)

    def __delitem__(self, key):
        property_url = self._dic["property"].replace("{key}", key)
        response, content = Request().delete(property_url)
        if response.status == 204:
            del self._dic["data"][key]
        elif response.status == 404:
            raise NotFoundError(response.status, "Node or property not found")
        else:
            raise StatusException(response.status, "Node or propery not found")

    def __len__(self):
        return len(self._dic["data"])

    def __iter__(self):
        return self._dic["data"].__iter__()

    def __eq__(self, obj):
        return (hasattr(obj, "url")
                and self.url == obj.url
                and hasattr(obj, "__class__")
                and self.__class__ == obj.__class__)

    def __ne__(self, obj):
        return not self.__cmp__(obj)

    def __nonzero__(self):
        return bool(self._dic)

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"<Neo4j %s: %s>" % (self.__class__.__name__, self.url)

    def _get_properties(self):
        return self._dic["data"]

    def _set_properties(self, props={}):
        if not props:
            return None
        properties_url = self._dic["properties"]
        response, content = Request().put(properties_url, data=props)
        if response.status == 204:
            self._dic["data"] = props.copy()
            return props
        elif response.status == 400:
            raise StatusException(response.status, "Invalid data sent")
        else:
            raise NotFoundError(response.status, "Properties not found")

    def _del_properties(self):
        properties_url = self._dic["properties"]
        response, content = Request().delete(properties_url)
        if response.status == 204:
            self._dic["data"] = {}
        else:
            raise NotFoundError(response.status, "Properties not found")
    properties = property(_get_properties, _set_properties, _del_properties)


class NodesProxy(dict):
    """
    Class proxy for node in order to allow get a node by id and
    create new nodes through calling.
    """

    def __init__(self, node, reference_node=None, node_index=None):
        self._node = node
        self._reference_node = reference_node
        self._node_index = node_index

    def __call__(self, **kwargs):
        reference = kwargs.pop("reference", False)
        if reference and self._reference_node:
            return Node(self._reference_node)
        else:
            return self.create(**kwargs)

    def __getitem__(self, key):
        if isinstance(key, (str, unicode)) and key.startswith(self._node):
            return Node(key)
        else:
            return Node("%s/%s/" % (self._node, key))

    def get(self, key, *args, **kwargs):
        try:
            return self.__getitem__(key)
        except (KeyError, NotFoundError, StatusException):
            if args:
                return args[0]
            elif "default" in kwargs:
                return kwargs["default"]
            else:
                raise NotFoundError()

    def create(self, **kwargs):
        return Node(self._node, create=True, data=kwargs)

    def delete(self, key):
        node = self.__getitem__(key)
        del node

    def _indexes(self):
        if self._node_index:
            return IndexesProxy(self._node_index, NODE)
    indexes = property(_indexes)


class Node(Base):
    """
    Node class.
    """

    def __getattr__(self, relationship_name, *args, **kwargs):
        """
        HACK: Allow to set node relationship
        """

        def relationship(to, *args, **kwargs):
            create_relationship_url = self._dic["create_relationship"]
            data = {
                "to": to.url,
                "type": relationship_name,
            }
            if kwargs:
                data.update({"data": kwargs})
            response, content = Request().post(create_relationship_url,
                                               data=data)
            if response.status == 201:
                return Relationship(response.get("location"))
            elif response.status == 404:
                raise NotFoundError(response.status, "Node specified by the " \
                                                     "URI not of \"to\" node" \
                                                     "not found")
            else:
                raise StatusException(response.status, "Invalid data sent")
        return relationship

    def _get_relationships(self):
        """
        HACK: Return a 3-methods class: incoming, outgoing and all.
        """
        return Relationships(self)
    relationships = property(_get_relationships)

    def _get_id(self):
        return int(self.url.split("/")[-1])
    id = property(_get_id)

    def traverse(self, types=None, order=None, stop=None, returnable=None,
                 uniqueness=None, is_stop_node=None, is_returnable=None,
                 returns=None):
        data = {}
        if order in (BREADTH_FIRST, DEPTH_FIRST):
            data.update({"order": order})
        if isinstance(stop, (int, float)) or stop is STOP_AT_END_OF_GRAPH:
            data.update({"max depth": stop})
        if returnable in (BREADTH_FIRST, DEPTH_FIRST):
            data.update({"return filter": {
                            "language": "builtin",
                            "name": returnable,
            }})
        if uniqueness in (NODE_GLOBAL, NODE_PATH, NODE_RECENT, NODE,
                          RELATIONSHIP_GLOBAL, RELATIONSHIP_PATH,
                          RELATIONSHIP_RECENT):
            data.update({"uniqueness": uniqueness})
        if types:
            if not isinstance(types, (list, tuple)):
                types = [types]
            relationships = []
            for relationship in types:
                if relationship.direction == "both":
                    relationships.append({"type": relationship.type})
                else:
                    relationships.append({"type": relationship.type,
                                          "direction": relationship.direction})
            if relationships:
                data.update({"relationships": relationships})
        if returns not in (NODE, RELATIONSHIP, PATH, POSITION):
            returns = NODE
        traverse_url = self._dic["traverse"].replace("{returnType}", returns)
        response, content = Request().post(traverse_url, data=data)
        if response.status == 200:
            results_list = json.loads(content)
            if returns is NODE:
                return [Node(r["self"]) for r in results_list]
            elif returns is RELATIONSHIP:
                return [Relationship(r["self"]) for r in results_list]
            elif returns is PATH:
                return [Path(r) for r in results_list]
            elif returns is POSITION:
                return [Position(r) for r in results_list]
        elif response.status == 404:
            raise NotFoundError(response.status, "Node or relationship not " \
                                                 "found")
        else:
            raise StatusException(response.status, "Invalid data sent")


class IndexesProxy(dict):
    """
    Class proxy for indexes (nodes and relationships).
    """

    def __init__(self, index_url, index_for=NODE):
        self.url = index_url
        self._index_for = index_for
        self._dict = self._get_dict()

    def __getitem__(self, attr):
        return self._dict[attr]

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return unicode(self._dict)

    def _get_dict(self):
        indexes_dict = {}
        response, content = Request().get(self.url)
        if response.status == 200:
            indexes_dict = json.loads(content)
            for index_name, index_properties in indexes_dict.items():
                indexes_dict[index_name] = Index(self._index_for, index_name,
                                                 **index_properties)
            return indexes_dict
        elif response.status == 404:
            raise NotFoundError(response.status, "Indexes not found")
        elif response.status == 204:
            return indexes_dict
        else:
            raise StatusException(response.status,
                                  "Error requesting indexes with GET %s" \
                                   % self.url)

    def create(self, name, **kwargs):
        data = {
            'name': name,
            'config': {
                'type': kwargs.get("type", INDEX_FULLTEXT),
                'provider': kwargs.get("provider", "lucene"),
            }
        }
        if name not in self._dict:
            response, content = Request().post(self.url, data=data)
            if response.status == 201:
                result_dict = json.loads(content)
                self._dict[name] = Index(self._index_for, name, **result_dict)
            else:
                raise StatusException(response.status, "Invalid data sent")
        return self._dict[name]

    def get(self, attr, *args, **kwargs):
        if attr in self._dict.keys():
            return self.__getitem__(attr)
        else:
            if args:
                return args[0]
            elif "default" in kwargs:
                return kwargs["default"]
            else:
                raise NotFoundError()

    def items(self):
        return self._dict.items()

    def values(self):
        return self._dict.values()

    def keys(self):
        return self._dict.keys()


class Index(object):
    """
    key/value indexed lookups. Create an index object with GraphDatabase.index.
    The returned object supports dict style lookups, eg index[key][value].
    """

    class IndexKey(object):
        """
        Intermediate object so that lookups can be done like:
        index[key][value]

        Lookups are formated as http://.../{index_name}/{key}/{value}, so this
        is the object that gets returned by index[key]. The REST request will
        be sent when the value is specified.
        """

        def __init__(self, index_for, url):
            self._index_for = index_for
            if url[-1] == '/':
                url = url[:-1]
            self.url = url

        def __getitem__(self, value):
            url = "%s/%s" % (self.url, value)
            return self._get_results(url)

        def __setitem__(self, value, item):
            # Neo4j hardly crush if you try to index a relationship in a
            # node index and viceversa.
            is_node_index = self._index_for == NODE and isinstance(item, Node)
            is_relationship_index = (self._index_for == RELATIONSHIP
                                     and isinstance(item, Relationship))
            if not (is_node_index or is_relationship_index):
                raise TypeError("%s is a %s and the index is for %ss"
                                % (item, self._index_for.capitalize(),
                                   self._index_for))
            value = urllib.quote(value)
            if isinstance(item, Base):
                url_ref = item.url
            else:
                url_ref = item
            request_url = "%s/%s" % (self.url, value)
            response, content = Request().post(request_url, data=url_ref)
            if response.status == 201:
                # Returns object that was indexed
                entity = json.loads(content)
                if self._index_for == NODE:
                    return Node(entity['self'], data=entity['data'])
                else:
                    return Relationship(entity['self'], data=entity['data'])
            else:
                raise StatusException(response.status,
                                      "Error requesting index with POST %s " \
                                      ", data %s" % (request_url, url_ref))

        def _get_results(self, url):
            response, content = Request().get(url)
            if response.status == 200:
                data_list = json.loads(content)
                if self._index_for == NODE:
                    return [Node(n['self'], data=n['data'])
                            for n in data_list]
                else:
                    return [Relationship(r['self'], data=r['data'])
                            for r in data_list]
            elif response.status == 404:
                raise NotFoundError(response.status,
                                    "Node or relationship not found")
            else:
                raise StatusException(response.status,
                                      "Error requesting index with GET %s" \
                                       % url)

        def query(self, value):
            url = "%s?query=%s" % (self.url, urllib.quote(value))
            return self._get_results(url)

    def __init__(self, index_for, name, **kwargs):
        self._index_for = index_for
        self.name = name
        self.template = kwargs.get("template")
        self.provider = kwargs.get("provider")
        self.type = kwargs.get("type")
        url = self.template.replace("{key}/{value}", "")
        if url[-1] == '/':
            url = url[:-1]
        self.url = url

    def __getitem__(self, key):
        return self.get(key)

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"<Neo4j %s: %s>" % (self.__class__.__name__, self.url)

    def add(self, key, value, item):
        self.get(key)[value] = item

    def get(self, key, value=None):
        key = urllib.quote(key)
        if value:
            return self.IndexKey(self._index_for,
                                 "%s/%s" % (self.url, key))[value]
        else:
            return self.IndexKey(self._index_for, "%s/%s" % (self.url, key))

    def delete(self, key, value, item):
        if not isinstance(item, Base):
            raise TypeError("%s has no url attribute" % item)
        if key and value:
            key = urllib.quote(key)
            value = urllib.quote(value)
            url = self.template.replace("{key}", key).replace("{value}", value)
            url = "%s/%s" % (url, item.id)
        elif key and not value:
            key = urllib.quote(key)
            url = "%s/%s" % (self.template.replace("{key}", key), item.id)
        elif not key and not value:
            url = self.template.replace("{key}/{value}", item.id)
        else:
            raise TypeError("remove() take at least 2 arguments, the key " \
                            "of the index and the %s to remove"
                            % self._index_for)
        response, content = Request().delete(url)
        if response.status == 404:
            raise NotFoundError(response.status,
                                "%s not found" % self._index_for.capitalize())
        elif response.status != 204:
            raise StatusException(response.status)

    def query(self, key, value):
        return self.get(key).query(value)


class RelationshipsProxy(dict):
    """
    Class proxy for relationships in order to allow get a relationship by id
    and create new relationships through calling.
    """

    def __init__(self, relationship, relationship_index):
        self._relationship = relationship
        self._relationship_index = relationship_index

    def __getitem__(self, key):
        return Relationship("%s/%s" % (self._relationship, key))

    def get(self, key, *args, **kwargs):
        try:
            return self.__getitem__(key)
        except (KeyError, NotFoundError, StatusException):
            if args:
                return args[0]
            elif "default" in kwargs:
                return kwargs["default"]
            else:
                raise NotFoundError()

    def create(self, node_from, relationship_name, node_to, **kwargs):
        return getattr(node_from, relationship_name)(node_to, **kwargs)

    def delete(self, key):
        relationship = self.__getitem__(key)
        del relationship

    def _indexes(self):
        if self._relationship_index:
            return IndexesProxy(self._relationship_index, RELATIONSHIP)
    indexes = property(_indexes)


class Relationships(object):
    """
    Relationships class for a node.
    """

    def __init__(self, node):
        self._node = node
        self._pattern = "{-list|&|types}"

    def __getattr__(self, relationship_type):

        def get_relationships(types=None, *args, **kwargs):
            if relationship_type in ["all", "incoming", "outgoing"]:
                if types and isinstance(types, (tuple, list)):
                    key = "%s_typed_relationships" % relationship_type
                    url_string = self._node._dic[key]
                    url = url_string.replace(self._pattern, "&".join(types))
                else:
                    key = "%s_relationships" % relationship_type
                    url = self._node._dic[key]
                response, content = Request().get(url)
                if response.status == 200:
                    relationship_list = json.loads(content)
                    relationships = [Relationship(r["self"])
                                     for r in relationship_list]
                    return relationships
                elif response.status == 404:
                    raise NotFoundError(response.status,
                                        "Node or relationship not found")
                else:
                    raise StatusException(response.status, "Node not found")
            raise NameError("name %s is not defined" % relationship_type)

        return get_relationships

    def create(self, relationship_name, to, **kwargs):
        return getattr(self._node, relationship_name)(to, **kwargs)


class Relationship(Base):
    """
    Relationship class.
    """

    def _get_start(self):
        return Node(self._dic['start'])
    start = property(_get_start)

    def _get_end(self):
        return Node(self._dic['end'])
    end = property(_get_end)

    def _get_type(self):
        return self._dic['type']
    type = property(_get_type)

    def _get_id(self):
        return int(self.url.split("/")[-1])
    id = property(_get_id)


class Path(object):
    """
    Path class for return type PATH in traversals.
    """

    def __init__(self, dic):
        self.start = property(Node(dic["start"]))
        self.end = property(Node(dic["end"]))
        self._length = int(dic["length"])
        nodes = []
        relationships = []
        self._iterable = []
        for i in range(0, len(dic["relationships"])):
            node = Node(dic["nodes"][i])
            nodes.append(node)
            relationship = Relationship(dic["relationships"][i])
            relationships.append(node)
            self._iterable.append(node)
            self._iterable.append(relationship)
        node = Node(dic["nodes"][-1])
        nodes.append(node)
        self._iterable.append(node)
        self.nodes = property(nodes)
        self.relationships = property(relationships)

    def __len__(self):
        return self._length

    def __iter__(self):
        while True:
            for obj in self._iterable:
                yield obj


class Position(object):
    """
    Position class for return type POSITION in traversals.
    """

    def __init__(self, dic):
        self.node = property(Node(dic["node"]))
        self.depth = int(dic["depth"])
        relationship = Relationship(dic["last relationship"])
        self.last_relationship = property(relationship)
        self.path = property(Path(dic["path"]))


class BaseInAndOut(object):
    """
    Base class for Incoming, Outgoing and Undirected relationships types.
    """

    def __init__(self, direction):
        self.direction = direction

    def get(self, attr):
        return self.__getattr__(attr)

    def __getattr__(self, attr):
        # Using an anonymous class
        direction = self.direction
        return type("", (object, ), {
            'direction': property(lambda self: direction),
            'type': property(lambda self: attr),
        })()

Outgoing = BaseInAndOut(direction="out")
Incoming = BaseInAndOut(direction="in")
Undirected = BaseInAndOut(direction="both")


class ExtensionsProxy(dict):
    """
    Class proxy for extensions in order to allow get an extension by module
    and class name and executing with the right params through calling.
    """

    def __init__(self, extensions):
        self._extensions = extensions
        self._dict = {}

    def __getitem__(self, attr):
        return self.__getattr__(attr)

    def __getattr__(self, attr):
        if attr in self._dict:
            return self._dict[attr]
        class_name = self._extensions[attr]
        # Using an anonymous class
        return type("ExtensionModule", (dict, ), {
            '__str__': lambda self: self.__unicode__(),
            '__repr__': lambda self: self.__unicode__(),
            '__unicode__': lambda self: u"<Neo4j %s: %s>" \
                                        % (self.__class__.__name__,
                                           unicode(class_name.keys())),
            '__getitem__': lambda self, _attr: self.__getattr__(_attr),
            '__getattr__': lambda self, _attr: Extension(class_name[_attr]),
            'get': lambda self, _attr: self.__getattr__(_attr),
        })()

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        if not self._dict:
            self._dict = self._get_dict()
        return unicode(self._dict)

    def _get_dict(self):
        return dict([(key, self.__getattr__(key))
                     for key in self._extensions.keys()])

    def get(self, attr, *args, **kwargs):
        if attr in self._dict.keys():
            return self.__getattr__(attr)
        else:
            if args:
                return args[0]
            elif "default" in kwargs:
                return kwargs["default"]
            else:
                raise NotFoundError()

    def items(self):
        if not self._dict:
            self._dict = self._get_dict()
        return self._dict.items()

    def values(self):
        if not self._dict:
            self._dict = self._get_dict()
        return self._dict.values()

    def keys(self):
        if not self._dict:
            self._dict = self._get_dict()
        return self._dict.keys()


class Extension(object):
    """
    Extension class.
    """

    def __init__(self, url):
        self._dic = {}
        if url.endswith("/"):
            url = url[:-1]
        self.url = url
        response, content = Request().get(self.url)
        if response.status == 200:
            self._dic.update(json.loads(content).copy())
            self.description = self._dic['description']
            self.name = self._dic['name']
            self.extends = self._dic['extends']
            self.parameters = self._dic['parameters']
        else:
            raise NotFoundError(response.status, "Unable get extension")

    def __call__(self, *args, **kwargs):
        parameters = self._parse_parameters(args, kwargs)
        response, content = Request().post(self.url, data=parameters)
        if response.status == 200:
            results_list = json.loads(content)
            # The returns param is a temporary solution while
            # a proper way to get the data type of returned values by
            # the extensions is implemented in Neo4j
            returns = kwargs.pop("returns", None)
            # Another option is to inspect the results
            if not returns and isinstance(results_list, (tuple, list)):
                returns = results_list[0].get("self", None)
            if results_list and returns:
                if NODE in returns:
                    return [Node(r["self"]) for r in results_list]
                elif RELATIONSHIP in returns:
                    return [Relationship(r["self"]) for r in results_list]
                elif PATH in returns:
                    return [Path(r) for r in results_list]
                elif POSITION in returns:
                    return [Position(r) for r in results_list]
            else:
                return []
        elif response.status == 404:
            raise NotFoundError(response.status, "Extension not found")
        else:
            raise StatusException(response.status, "Invalid data sent")

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"<Neo4j %s: %s>" % (self.__class__.__name__, self.url)

    def _parse_parameters(self, args, kwargs):
        if not args and not kwargs:
            return kwargs
        params_len = len(self.parameters)
        args_len = len(args)
        kwargs_len = len(kwargs)
        if args_len + kwargs_len > params_len:
            raise TypeError("%s() take at most %s arguments (%s given)"
                            % (self.name, params_len, args_len + kwargs_len))
        required = [np for np in self.parameters if np["optional"] == False]
        required_len = len(required)
        if args_len + kwargs_len < required_len:
            raise TypeError("%s() take at least %s arguments (%s given)"
                            % (self.name, required_len, args_len + kwargs_len))
        params_kwargs = {}
        if args:
            for i, arg in enumerate(args):
                key = required[i]["name"]
                params_kwargs[key] = args[i]
        if kwargs:
            for param, value in kwargs.items():
                has_param = (len([np for np in self.parameters
                                     if np["name"] == param]) != 0)
                if key not in params_kwargs and has_param:
                    params_kwargs[key] = value
        return self._parse_types(params_kwargs)

    def _parse_types(self, kwargs):
        params_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, Base):
                params_kwargs[key] = value.url
            else:
                params_kwargs[key] = value
        return params_kwargs
