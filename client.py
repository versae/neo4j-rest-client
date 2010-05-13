# -*- coding: utf-8 -*-
import datetime
import decimal
import httplib
import base64
import simplejson
from urlparse import urlsplit

__all__ = ("GraphDatabase", )


class GraphDatabase(object):
    """
    Main class for connection to Ne4j standalone REST server.
    """
    url = None
    node = {}
    index_url = None
    reference_node_url = None
    index_path = "/index"
    node_path = "/node"

    def __init__(self, url):
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
            self.node = NodeProxy(self.url, self.node_path,
                                  self.reference_node_url)
        else:
            raise StatusException(response.status, "Unable get root")

    def _get_reference_node(self):
        return Node(self.reference_node_url)
    reference_node = property(_get_reference_node)

    def index(self, create=False):
        pass


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

    def __call__(self, *args, **kwargs):
        reference = kwargs.pop("reference", False)
        if reference and self.reference_node_url:
            return Node(self.reference_node_url)
        else:
            return self.create(**kwargs)

    def __getitem__(self, key):
        return Node("%s/%s" % (self.node_url, key))

    def get(self, key):
        return self.__getitem__(key)

    def create(self, **kwargs):
        return Node(self.node_url, create=True, data=kwargs)


class Node(object):
    """
    Node class.
    """
    url = None
    dic = {}

    def __init__(self, url, create=False, data={}):
        if create:
            response = Request().post(url, data=data)
            if response.status == 201:
                self.dic.update(data)
                self.url = response.getheader("Location")
            else:
                raise StatusException(response.status, "Invalid data sent")
        if not self.url:
            self.url = url
        response = Request().get(self.url)
        if response.status == 200:
            content = response.body
            self.dic.update(simplejson.loads(content))
        else:
            raise StatusException(response.status, "Unable get node")

    def __getitem__(self, key):
        property_url = self.dic["property"].replace("{key}", key)
        response = Request().get(property_url)
        if response.status == 200:
            content = response.body
            self.dic["data"][key] = simplejson.loads(content)
        else:
            raise StatusException(response.status, "Node or propery not found")
        return self.dic["data"][key]

    def __setitem__(self, key, value):
        property_url = self.dic["property"].replace("{key}", key)
        response = Request().put(property_url, data=value)
        if response.status == 204:
            self.dic["data"].update({key: value})
        else:
            raise StatusException(response.status, "Invalid data sent")

    def __deleteitem__(self, key):
        property_url = self.dic["property"].replace("{key}", key)
        response = Request().delete(property_url)
        if response.status == 204:
            del self.dic["data"][key]
        else:
            raise StatusException(response.status, "Node or propery not found")

    def __getattr__(self, relationship_name, *args, **kwargs):
        """HACK: To allow to set node relationship"""

        def relationship(to, *args, **kwargs):
            create_relationship_url = self.dic["create relationship"]
            data = {
                "to": to.url,
                "type": relationship_name,
            }
            if kwargs:
                data.update({"data": kwargs})
            response = Request().post(create_relationship_url, data=data)
            if response.status == 201:
                # TODO: Return RelationShip with returned location
                # return RelationShip(response.getheader("Location"))
                return response.getheader("Location")
            else:
                raise StatusException(response.status,
                                      "Invalid data sent, \"to\" node, or " \
                                      "the node specified by the URI not " \
                                      "found")
            print create_relationship_url, relationship_name, to, args, kwargs
        return relationship

    def __unicode__(self):
        return u"<Neo4j Node: >" % self.url

    def properties(self):
        return self.dic["data"]


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

    def _json_encode(data, ensure_ascii=False):

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
            connection = httplib.HTTPSConnection(hostname, port,
                                                  self.key_file,
                                                  self.cert_file)
        else:
            connection = httplib.HTTPConnection(hostname, port)
        headers = headers or {}
        headers['Accept'] = 'application/json'
        headers['Accept-Encoding'] = '*'
        headers['Content-Type'] = 'application/json'

        if username and password:
            credentials = "%s:%s" % (username, password)
            base64_credentials = base64.encodestring(credentials)
            authorization = "Basic %s" % base64_credentials[:-1]
            headers['Authorization'] = authorization

        body = self._json_encode(data)
        connection.request(method, url, body, headers)
        response = connection.getresponse()
        response.body = response.read()
        connection.close()
        if response.status == 401:
            raise StatusException(401, "Authorization Required")
        return response
