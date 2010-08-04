# -*- coding: utf-8 -*-
import base64
import datetime
import decimal
import httplib
import re
import simplejson
import time
from urlparse import urlsplit
import urllib

__all__ = ("GraphDatabase", "Incoming", "Outgoing", "Undirected",
           "StopAtDepth", "NotFoundError", "StatusException")
__author__ = "Javier de la Rosa, and Diego Muñoz Escalante"
__credits__ = ["Javier de la Rosa", "Diego Muñoz Escalante"]
__license__ = "GPLv3"
__version__ = "0.0.1"
__email__ = "versae [at] gmail [dot] com"
__status__ = "Development"


# Order
BREADTH_FIRST = "breadth first"
DEPTH_FIRST = "depth first"
# Return
RETURN_ALL_NODES = "all"
RETURN_ALL_BUT_START_NODE = "all but start node"
# Stop
STOP_AT_DEPTH_ONE = 1
STOP_AT_END_OF_GRAPH = "none"
# Uniqueness
NODE_GLOBAL = "node global"
NODE_PATH = "node path"
NODE_RECENT = "node recent"
RELATIONSHIP_GLOBAL = "relationship global"
RELATIONSHIP_PATH = "relationship path"
RELATIONSHIP_RECENT = "relationship recent"
# Returns
NODE = "node"
RELATIONSHIP = "relationship"
PATH = "path"
POSITION = "position"


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
        self.node = {}
        self.index_url = None
        self.reference_node_url = None
        self.index_path = "/index"
        self.node_path = "/node"
        self.Traversal = self._get_traversal_class()
        self.Index = Index()
        if url.endswith("/"):
            self.url = url[0:-1]
        else:
            self.url = url
            
        self._get_nodes(url)

    def _get_nodes(self, url):
        response = Request().get(url)
        if response.status == 200:
            content = response.body
            response_json = simplejson.loads(content)
            self.index_url = response_json['index']
            self.reference_node_url = response_json['reference node']
            self.nodes = NodeProxy(self.url, self.node_path,
                                  self.reference_node_url,
                                  index_url=self.index_url)
            # Backward compatibility. The current style is more pythonic
            self.node = self.nodes
        else:
            raise NotFoundError(response.status, "Unable get root")

    def _get_reference_node(self):
        return Node(self.reference_node_url)
    reference_node = property(_get_reference_node)

    def index(self, key, value=None, create=None):
        self.Index.index_url = self.index_url
        self.Index.nodes = self.nodes
        return self.Index.mediate(key, value=value, create=create)        

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
        
class Index(object):
    nodes = {}
    index_url = ''
      
    def mediate(self, key, value=None, create=None):
        if create:
            return self.create(key)
        else:
            return self.get(key, value)
        
    def create(self, key):
        for ind in self.nodes:
            node = self.nodes[ind]
            create = '%s/node/%s/%s' % (self.index_url, urllib.quote(key), urllib.quote(node.get(key)))
            response = Request().post(create, data=node.url, headers=False)
            if response.status == 201:
                if response.body:
                    self._dic["indexed"] = response.body
            else:
                raise NotFoundError(response.status, "Problem?")
            
        return self
        
    def get(self, key, value):
        nodes = []
        get = '%s/node/%s/%s' % (self.index_url, key, urllib.quote(value))
        response = Request().get(get)
        
        if response.status == 200:
            content = response.body
            nodes = simplejson.loads(content)
            print nodes
        else:
            raise StatusException(response.status)
                
        return nodes
        
    def delete(self):
        pass

class Base(object):
    """
    Base class.
    """

    def __init__(self, url, index_url=None, create=False, data={}):
        self._dic = {}
        self.url = None
        self.Index = Index()
        self.Index.index_url = index_url
        self.Index.nodes = {self.id: self}
        if create:
            response = Request().post(url, data=data)
            if response.status == 201:
                self._dic.update(data.copy())
                self.url = response.getheader("Location")
            else:
                raise NotFoundError(response.status, "Invalid data sent")
        if not self.url:
            self.url = url
        response = Request().get(self.url)
        if response.status == 200:
            content = response.body
            self._dic.update(simplejson.loads(content).copy())
        else:
            raise NotFoundError(response.status, "Unable get node")

    def delete(self, key=None):
        if key:
            self.__delitem__(key)
            return
        response = Request().delete(self.url)
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
        response = Request().get(property_url)
        if response.status == 200:
            content = response.body
            self._dic["data"][key] = simplejson.loads(content)
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
    
    def index(self, key, create=False):
        return self.Index.mediate(key, create=create)
    
    def __contains__(self, obj):
        return obj in self._dic["data"]

    def __setitem__(self, key, value):
        property_url = self._dic["property"].replace("{key}", key)
        response = Request().put(property_url, data=value)
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
        response = Request().delete(property_url)
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
        response = Request().put(properties_url, data=props)
        if response.status == 204:
            self._dic["data"] = props.copy()
            return props
        elif response.status == 400:
            raise StatusException(response.status, "Invalid data sent")
        else:
            raise NotFoundError(response.status, "Properties not found")

    def _del_properties(self):
        properties_url = self._dic["properties"]
        response = Request().delete(properties_url)
        if response.status == 204:
            self._dic["data"] = {}
        else:
            raise NotFoundError(response.status, "Properties not found")
    properties = property(_get_properties, _set_properties, _del_properties)


class NodeProxy(dict):
    """
    Class proxy for node in order to allow get a node by id and
    create new nodes through calling.
    """

    def __init__(self, url, node_path, reference_node_url=None, index_url=None):
        self.url = url
        self.node_path = node_path
        self.node_url = "%s%s" % (self.url, self.node_path)
        self.reference_node_url = reference_node_url
        self.index_url = index_url

    def __call__(self, **kwargs):
        reference = kwargs.pop("reference", False)
        if reference and self.reference_node_url:
            return Node(self.reference_node_url, index_url=self.index_url)
        else:
            return self.create(**kwargs)

    def __getitem__(self, key):
        if isinstance(key, (str, unicode)) and key.startswith(self.node_url):
            return Node(key, index_url=self.index_url)
        else:
            return Node("%s/%s" % (self.node_url, key), index_url=self.index_url)

    def get(self, key):
        return self.__getitem__(key)

    def create(self, **kwargs):
        node = Node(self.node_url, index_url=self.index_url, create=True, data=kwargs)
        self[node.id] = node
        return self[node.id]

    def delete(self, key):
        node = self.__getitem__(key)
        del node


class Node(Base):
    """
    Node class.
    """

    def __getattr__(self, relationship_name, *args, **kwargs):
        """
        HACK: Allow to set node relationship
        """

        def relationship(to, *args, **kwargs):
            create_relationship_url = self._dic["create relationship"]
            data = {
                "to": to.url,
                "type": relationship_name,
            }
            if kwargs:
                data.update({"data": kwargs})
            response = Request().post(create_relationship_url, data=data)
            if response.status == 201:
                return Relationship(response.getheader("Location"))
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
        response = Request().post(traverse_url, data=data)
        if response.status == 200:
            content = response.body
            results_list = simplejson.loads(content)
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
                    key = "%s typed relationships" % relationship_type
                    url_string = self._node._dic[key]
                    url = url_string.replace(self._pattern, "&".join(types))
                else:
                    key = "%s relationships" % relationship_type
                    url = self._node._dic[key]
                response = Request().get(url)
                if response.status == 200:
                    content = response.body
                    relationship_list = simplejson.loads(content)
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


class StatusException(Exception):
    """
    Create an Error Response.
    """

    def __init__(self, value, result=None):
        self.value = value
        self.responses = {
        100: ('Continue', 'Request received, please continue'),
        101: ('Switching Protocols',
              'Switching to new protocol; obey Upgrade header'),
        200: ('OK', 'Request fulfilled, document follows'),
        201: ('Created', 'Document created, URL follows'),
        202: ('Accepted',
              'Request accepted, processing continues off-line'),
        203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
        204: ('No Content', 'Request fulfilled, nothing follows'),
        205: ('Reset Content', 'Clear input form for further input.'),
        206: ('Partial Content', 'Partial content follows.'),
        300: ('Multiple Choices',
              'Object has several resources -- see URI list'),
        301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
        302: ('Found', 'Object moved temporarily -- see URI list'),
        303: ('See Other', 'Object moved -- see Method and URL list'),
        304: ('Not Modified',
              'Document has not changed since given time'),
        305: ('Use Proxy',
              'You must use proxy specified in Location to access this '
              'resource.'),
        307: ('Temporary Redirect',
              'Object moved temporarily -- see URI list'),
        400: ('Bad Request',
              'Bad request syntax or unsupported method'),
        401: ('Unauthorized',
              'No permission -- see authorization schemes'),
        402: ('Payment Required',
              'No payment -- see charging schemes'),
        403: ('Forbidden',
              'Request forbidden -- authorization will not help'),
        404: ('Not Found', 'Nothing matches the given URI'),
        405: ('Method Not Allowed',
              'Specified method is invalid for this server.'),
        406: ('Not Acceptable', 'URI not available in preferred format.'),
        407: ('Proxy Authentication Required', 'You must authenticate with '
              'this proxy before proceeding.'),
        408: ('Request Timeout', 'Request timed out; try again later.'),
        409: ('Conflict', 'Request conflict.'),
        410: ('Gone',
              'URI no longer exists and has been permanently removed.'),
        411: ('Length Required', 'Client must specify Content-Length.'),
        412: ('Precondition Failed', 'Precondition in headers is false.'),
        413: ('Request Entity Too Large', 'Entity is too large.'),
        414: ('Request-URI Too Long', 'URI is too long.'),
        415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
        416: ('Requested Range Not Satisfiable',
              'Cannot satisfy request range.'),
        417: ('Expectation Failed',
              'Expect condition could not be satisfied.'),
        500: ('Internal Server Error', 'Server got itself in trouble'),
        501: ('Not Implemented',
              'Server does not support this operation'),
        502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
        503: ('Service Unavailable',
              'The server cannot process the request due to a high load'),
        504: ('Gateway Timeout',
              'The gateway server did not receive a timely response'),
        505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
        }
        if result:
            self.result = "\n%s" % result

    def __str__(self):
        return u"Error [%s]: %s. %s.%s" % (self.value,
                                           self.responses[self.value][0],
                                           self.responses[self.value][1],
                                           self.result)

    def __unicode__(self):
        return self.__str__()


class NotFoundError(StatusException):

    def __init__(self, value=None, result=None):
        if not value:
            value = 404
        if not result:
            result = "Node, relationship or property not found"
        super(NotFoundError, self).__init__(value, result)


class Request(object):
    """
    Create an HTTP request object for HTTP
    verbs GET, POST, PUT and DELETE.
    """

    def __init__(self, username=None, password=None, key_file=None,
                 cert_file=None):
        self.username = username
        self.password = password
        self.key_file = key_file
        self.cert_file = cert_file
        self._illegal_s = re.compile(r"((^|[^%])(%%)*%s)")

    def get(self, url, headers=None):
        """
        Perform an HTTP GET request for a given URL.
        Returns the response object.
        """
        return self._request('GET', url, headers=headers)

    def post(self, url, data, headers=None):
        """
        Perform an HTTP POST request for a given url.
        Returns the response object.
        """
        return self._request('POST', url, data, headers=headers)

    def put(self, url, data, headers=None):
        """
        Perform an HTTP PUT request for a given url.
        Returns the response object.
        """
        return self._request('PUT', url, data, headers=headers)

    def delete(self, url, headers=None):
        """
        Perform an HTTP DELETE request for a given url.
        Returns the response object.
        """
        return self._request('DELETE', url, headers=headers)

    # Proleptic Gregorian dates and strftime before 1900 « Python recipes
    # ActiveState Code: http://bit.ly/9t0JKb via @addthis

    def _findall(self, text, substr):
        # Also finds overlaps
        sites = []
        i = 0
        while 1:
            j = text.find(substr, i)
            if j == -1:
                break
            sites.append(j)
            i = j + 1
        return sites

    # Every 28 years the calendar repeats, except through century leap
    # years where it's 6 years.  But only if you're using the Gregorian
    # calendar.  ;)

    def _strftime(self, dt, fmt):
        if self._illegal_s.search(fmt):
            raise TypeError("This strftime implementation does not handle %s")
        if dt.year > 1900:
            return dt.strftime(fmt)
        year = dt.year
        # For every non-leap year century, advance by
        # 6 years to get into the 28-year repeat cycle
        delta = 2000 - year
        off = 6 * (delta // 100 + delta // 400)
        year = year + off
        # Move to around the year 2000
        year = year + ((2000 - year) // 28) * 28
        timetuple = dt.timetuple()
        s1 = time.strftime(fmt, (year,) + timetuple[1:])
        sites1 = self._findall(s1, str(year))
        s2 = time.strftime(fmt, (year + 28,) + timetuple[1:])
        sites2 = self._findall(s2, str(year + 28))
        sites = []
        for site in sites1:
            if site in sites2:
                sites.append(site)
        s = s1
        syear = "%4d" % (dt.year, )
        for site in sites:
            s = s[:site] + syear + s[site + 4:]
        return s

    def _json_encode(self, data, ensure_ascii=False):

        def _any(data):
            DATE_FORMAT = "%Y-%m-%d"
            TIME_FORMAT = "%H:%M:%S"
            ret = None
            if isinstance(data, (list, tuple)):
                ret = _list(data)
            elif isinstance(data, dict):
                ret = _dict(data)
            elif isinstance(data, decimal.Decimal):
                ret = str(data)
            elif isinstance(data, datetime.datetime):
                ret = self._strftime(data,
                                     "%s %s" % (DATE_FORMAT, TIME_FORMAT))
            elif isinstance(data, datetime.date):
                ret = self._strftime(data, DATE_FORMAT)
            elif isinstance(data, datetime.time):
                ret = data.strftime(TIME_FORMAT)
            else:
                ret = data
            return ret

        def _list(data):
            ret = []
            for v in data:
                ret.append(_any(v))
            return ret

        def _dict(data):
            ret = {}
            for k, v in data.items():
                # Neo4j doesn't allow 'null' properties
                if v:
                    ret[k] = _any(v)
            return ret
        ret = _any(data)
        return simplejson.dumps(ret, ensure_ascii=ensure_ascii)

    def _request(self, method, url, data={}, headers={}):
        splits = urlsplit(url)
        scheme = splits.scheme
        hostname = splits.hostname
        port = splits.port
        username = splits.username or self.username
        password = splits.password or self.password
        if scheme.lower() == 'https':
            connection = httplib.HTTPSConnection(hostname, port, self.key_file,
                                                 self.cert_file)
        else:
            connection = httplib.HTTPConnection(hostname, port)
        headers = headers or {}
        headers['Accept'] = 'application/json'
        headers['Accept-Encoding'] = '*'
        headers['Accept-Charset'] = 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'
        headers['Content-Type'] = 'application/json'
        headers['User-Agent'] = 'Neo4jPythonClient/%s ' % __version__
        if username and password:
            credentials = "%s:%s" % (username, password)
            base64_credentials = base64.encodestring(credentials)
            authorization = "Basic %s" % base64_credentials[:-1]
            headers['Authorization'] = authorization
            headers['Remote-User'] = username
        # dont json encode body when it starts with http://. for set 
        # index property
        if isinstance(data, str) and data.startswith('http://'):
            body = data
        else:
            body = self._json_encode(data, ensure_ascii=True)
        connection.request(method, url, body, headers)
        response = connection.getresponse()
        response.body = response.read()
        connection.close()
        if response.status == 401:
            raise StatusException(401, "Authorization Required")
        return response