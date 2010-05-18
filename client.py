# -*- coding: utf-8 -*-
import datetime
import decimal
import httplib
import base64
import simplejson
from urlparse import urlsplit

__all__ = ("GraphDatabase", )
__version__ = u'0.1alpha'


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
        if url.endswith("/"):
            self.url = url[0:-1]
        else:
            self.url = url
        response = Request().get(url)
        if response.status == 200:
            content = response.body
            response_json = simplejson.loads(content)
            self.index_url = response_json['index']
            self.reference_node_url = response_json['reference node']
            self.nodes = NodeProxy(self.url, self.node_path,
                                  self.reference_node_url)
            # Backward compatibility. The current style is more pythonic
            self.node = self.nodes
        else:
            raise StatusException(response.status, "Unable get root")

    def _get_reference_node(self):
        return Node(self.reference_node_url)
    reference_node = property(_get_reference_node)

    def index(self, create=False):
        pass


class Base(object):
    """
    Base class.
    """

    def __init__(self, url, create=False, data={}):
        self._dic = {}
        self.url = None
        if create:
            response = Request().post(url, data=data)
            if response.status == 201:
                self._dic.update(data.copy())
                self.url = response.getheader("Location")
            else:
                raise StatusException(response.status, "Invalid data sent")
        if not self.url:
            self.url = url
        response = Request().get(self.url)
        if response.status == 200:
            content = response.body
            self._dic.update(simplejson.loads(content).copy())
        else:
            raise StatusException(response.status, "Unable get node")

    def delete(self):
        response = Request().delete(self.url)
        if response.status == 204:
            del self
        else:
            raise StatusException(response.status, "Node not found or node" \
                                                   "could not be deleted "\
                                                   "(still has " \
                                                   "relationships?) " \
                                                   "node not found")

    def __getitem__(self, key):
        property_url = self._dic["property"].replace("{key}", key)
        response = Request().get(property_url)
        if response.status == 200:
            content = response.body
            self._dic["data"][key] = simplejson.loads(content)
        else:
            raise StatusException(response.status, "Node or propery not found")
        return self._dic["data"][key]

    def get(self, key, *args):
        if args:
            default = args[0]
            try:
                return self.__getitem__(key)
            except (KeyError, StatusException):
                return default
        else:
            return self.__getitem__(key)

    def __contains__(self, obj):
        return obj in self._dic["data"]

    def __setitem__(self, key, value):
        property_url = self._dic["property"].replace("{key}", key)
        response = Request().put(property_url, data=value)
        if response.status == 204:
            self._dic["data"].update({key: value})
        else:
            raise StatusException(response.status, "Invalid data sent")

    def set(self, key, value):
        self.__setitem__(key, value)

    def __delitem__(self, key):
        property_url = self._dic["property"].replace("{key}", key)
        response = Request().delete(property_url)
        if response.status == 204:
            del self._dic["data"][key]
        else:
            raise StatusException(response.status, "Node or propery not found")

    def delete(self, key):
        self.__delitem__(key)

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
        return bool(self._dic["data"])

    def __repr__(self):
        return u"<Neo4j %s: %s>" % (self.__class__.__name__, self.url)

    def __str__(self):
        return u"<Neo4j %s: %s>" % (self.__class__.__name__, self.url)

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
        else:
            raise StatusException(response.status, "Invalid data sent or " \
                                                   "node not found")

    def _del_properties(self):
        properties_url = self._dic["properties"]
        response = Request().delete(properties_url)
        if response.status == 204:
            self._dic["data"] = {}
        else:
            raise StatusException(response.status, "Invalid data sent or " \
                                                   "node not found")
    properties = property(_get_properties, _set_properties, _del_properties)


class NodeProxy(dict):
    """
    Class proxy for node in order to allow get a node by id and
    create new nodes through calling.
    """

    def __init__(self, url, node_path, reference_node_url=None):
        self.url = url
        self.node_path = node_path
        self.node_url = "%s%s" % (self.url, self.node_path)
        self.reference_node_url = reference_node_url

    def __call__(self, **kwargs):
        reference = kwargs.pop("reference", False)
        if reference and self.reference_node_url:
            return Node(self.reference_node_url)
        else:
            return self.create(**kwargs)

    def __getitem__(self, key):
        if isinstance(key, (str, unicode)) and key.startswith(self.node_url):
            return Node(key)
        else:
            return Node("%s/%s" % (self.node_url, key))

    def get(self, key):
        return self.__getitem__(key)

    def create(self, **kwargs):
        return Node(self.node_url, create=True, data=kwargs)

    def delete(self, key):
        node = self.__getitem__(key)
        del node


class Node(Base):
    """
    Node class.
    """

    def __getattr__(self, relationship_name, *args, **kwargs):
        """
        HACK: To allow to set node relationship
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
            else:
                raise StatusException(response.status,
                                      "Invalid data sent, \"to\" node, or " \
                                      "the node specified by the URI not " \
                                      "found")
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


class Relationships(object):
    """
    Relationships class for a node
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
                else:
                    raise StatusException(response.status, "Node not found")
            raise NameError("name %s is not defined" % relationship_type)

        return get_relationships

    def create(self, relationship_name, to, **kwargs):
        return getattr(self._node, relationship_name)(to, **kwargs)


class Relationship(Base):
    """
    Relationship class
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
        return "Error [%s]: %s. %s.%s" % (self.value,
            self.responses[self.value][0], self.responses[self.value][1],
            self.result)


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
                ret = data.strftime("%s %s" % (DATE_FORMAT, TIME_FORMAT))
            elif isinstance(data, datetime.date):
                ret = data.strftime(DATE_FORMAT)
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
        body = self._json_encode(data, ensure_ascii=True)
        connection.request(method, url, body, headers)
        response = connection.getresponse()
        response.body = response.read()
        connection.close()
        if response.status == 401:
            raise StatusException(401, "Authorization Required")
        return response
