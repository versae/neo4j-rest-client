# -*- coding: utf-8 -*-
import datetime
import decimal
import re
import requests
import json
import time

from neo4jrestclient import options
from neo4jrestclient.constants import __version__
from neo4jrestclient.exceptions import StatusException
from neo4jrestclient.utils import string_types, get_auth_from_uri

if options.DEBUG:
    import httplib
    import logging
    httplib.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
session = requests.Session()

if options.CACHE:
    try:
        from cachecontrol import CacheControl
        from cachecontrol.cache import DictCache
        from cachecontrol.caches import FileCache
    except ImportError as e:
        raise ImportError("CacheControl and lockfile need to be installed "
                          "in order to use CACHE and CACHE_STORE options "
                          "in neo4jrestclient. \n"
                          "Please, run $ pip install CacheControl lockfile")
    if isinstance(options.CACHE_STORE, string_types):
        cache = FileCache(options.CACHE_STORE)
    elif isinstance(options.CACHE_STORE, dict):
        cache = DictCache(options.CACHE_STORE)
    else:
        cache = options.CACHE_STORE
    session = CacheControl(session, cache=cache)


class Request(object):
    """
    Create an HTTP request object for HTTP
    verbs GET, POST, PUT and DELETE.
    """

    def __init__(self, username=None, password=None, key_file=None,
                 cert_file=None, **kwargs):
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
            ret = None
            if isinstance(data, (list, tuple)):
                ret = _list(data)
            elif isinstance(data, dict):
                ret = _dict(data)
            elif isinstance(data, decimal.Decimal):
                ret = str(data)
            elif isinstance(data, datetime.datetime):
                ret = self._strftime(data, options.DATETIME_FORMAT)
            elif isinstance(data, datetime.date):
                ret = self._strftime(data, options.DATE_FORMAT)
            elif isinstance(data, datetime.time):
                ret = data.strftime(options.TIME_FORMAT)
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
                if v is not None:
                    ret[k] = _any(v)
            return ret
        ret = _any(data)
        return json.dumps(ret, ensure_ascii=ensure_ascii)

    def _request(self, method, url, data={}, headers={}):
        username_uri, password_uri, root_uri = get_auth_from_uri(url)
        username = username_uri or self.username
        password = password_uri or self.password
        cert = None
        if self.cert_file:
            if self.key_file:
                cert = (self.cert_file, self.key_file)
            else:
                cert = self.cert_file
        headers = headers or {}
        headers['Accept'] = 'application/json; charset=UTF-8'
        headers['Accept-Encoding'] = '*'
        headers['Accept-Charset'] = 'UTF-8,ISO-8859-1;q=0.7,*;q=0.7'
        headers['Connection'] = 'keep-alive'
        if not options.CACHE:
            headers['Cache-Control'] = 'no-cache'
        headers['User-Agent'] = 'neo4jrestclient/%s ' % __version__
        auth = None
        if username and password:
            auth = (username, password)
        if method in ("POST", "PUT"):
            headers['Content-Type'] = 'application/json'
        data = self._json_encode(data, ensure_ascii=True)
        verify = options.VERIFY_SSL
        try:
            method = method.lower()
            response = getattr(session, method)(root_uri, headers=headers,
                                                data=data, cert=cert,
                                                auth=auth, verify=verify)
            if response.status_code == 401:
                raise StatusException(401, "Authorization Required")
            return response
        except AttributeError:
            raise Exception("Unknown error. Is the server running?")
