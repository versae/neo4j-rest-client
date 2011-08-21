# -*- coding: utf-8 -*-
import base64
import datetime
import decimal
import httplib2
import re
import json
import time
from urlparse import urlsplit

import options
from constants import __version__


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
        418: ('I\'m a teapot', 'Is the server running?'),
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
        else:
            self.result = None # pedantic, but needed for __str__()

    def __str__(self):
        return u"Error [%s]: %s. %s.%s" % (self.value,
                                           self.responses[self.value][0],
                                           self.responses[self.value][1],
                                           self.result)

    def __unicode__(self):
        return self.__str__()


class TransactionException(StatusException):

    def __init__(self, value=None):
        result = "Node, relationship or property not found"
        super(TransactionException, self).__init__(value, result)


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
                if v != None:
                    ret[k] = _any(v)
            return ret
        ret = _any(data)
        return json.dumps(ret, ensure_ascii=ensure_ascii)

    def _request(self, method, url, data={}, headers={}):
        splits = urlsplit(url)
        scheme = splits.scheme
        # Not used, it makes pyflakes happy
        # hostname = splits.hostname
        # port = splits.port
        username = splits.username or self.username
        password = splits.password or self.password
        headers = headers or {}
        if options.DEBUG:
            httplib2.debuglevel = 1
        else:
            httplib2.debuglevel = 0
        if options.CACHE:
            headers['Cache-Control'] = 'no-cache'
            http = httplib2.Http(".cache")
        else:
            http = httplib2.Http()
        if scheme.lower() == 'https':
            http.add_certificate(self.key_file, self.cert_file, self.url)
        headers['Accept'] = 'application/json'
        headers['Accept-Encoding'] = '*'
        headers['Accept-Charset'] = 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'
        # I'm not sure on the right policy about cache with Neo4j REST Server
        # headers['Cache-Control'] = 'no-cache'
        # TODO: Handle all requests with the same Http object
        headers['Connection'] = 'close'
        headers['User-Agent'] = 'Neo4jPythonClient/%s ' % __version__
        if username and password:
            credentials = "%s:%s" % (username, password)
            base64_credentials = base64.encodestring(credentials)
            authorization = "Basic %s" % base64_credentials[:-1]
            headers['Authorization'] = authorization
            headers['Remote-User'] = username
        if method in ("POST", "PUT"):
            headers['Content-Type'] = 'application/json'
        # Thanks to Yashh: http://bit.ly/cWsnZG
        # Don't JSON encode body when it starts with "http://" to set inde
        # hrm, neo4j-1.3.M04 always expects JSON
        # if isinstance(data, basestring) and data.startswith('http://'):
        #    body = data
        # else:
        body = self._json_encode(data, ensure_ascii=True)
        try:
            response, content = http.request(url, method, headers=headers,
                                             body=body)
            if response.status == 401:
                raise StatusException(401, "Authorization Required")
            return response, content
        except AttributeError:
            raise Exception("Unknown error. Is the server running?")
