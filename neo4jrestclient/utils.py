# -*- coding: utf-8 -*-
import json
import sys
PYTHON_VERSION = sys.version_info
PY2 = sys.version_info[0] == 2

if PY2:
    import urllib
    from urlparse import urlparse
    quote = urllib.quote
    unquote = urllib.unquote
    text_type = unicode
    string_types = (str, unicode)
    unichr = unichr

    def smart_quote(val):
        if isinstance(val, (bool, int, long)):
            return quote(json.dumps(val), safe="")
        elif isinstance(val, float):
            return unicode(val)
        else:
            try:
                safe_key = quote(val, safe="")
            except (KeyError, UnicodeEncodeError, UnicodeError):
                safe_key = quote(val.encode("utf8"), safe="")
            return safe_key

else:
    from urllib.parse import quote, unquote, urlparse
    quote = quote
    unquote = unquote
    text_type = str
    string_types = (str,)
    unichr = chr

    def smart_quote(val):
        if isinstance(val, (bool, int, float)):
            return quote(json.dumps(val), safe="")
        else:
            try:
                safe_key = quote(val, safe="")
            except (KeyError, UnicodeEncodeError, UnicodeError):
                safe_key = quote(val.encode("utf8"), safe="")
            return safe_key


def in_ipnb():
    """
    check if we're inside an IPython Notebook
    https://github.com/pydata/pandas/blob/master/pandas/core/common.py#L2508
    """
    try:
        ip = get_ipython()
        front_end = (
            ip.config.get('KernelApp', {}).get('parent_appname', "") or
            ip.config.get('IPKernelApp', {}).get('parent_appname', "")
        )
        if 'notebook' in front_end.lower():
            return True
    except:
        return False
    return False


def get_auth_from_uri(uri):
    splits = urlparse(uri)
    if splits.port:
        port = u":%s" % splits.port
    else:
        port = u""
    if splits.query and splits.fragment:
        root_uri = "%s://%s%s%s?%s#%s" % (splits.scheme, splits.hostname,
                                          port, splits.path,
                                          splits.query, splits.fragment)
    elif splits.query:
        root_uri = "%s://%s%s%s?%s" % (splits.scheme, splits.hostname,
                                       port, splits.path,
                                       splits.query)
    elif splits.fragment:
        root_uri = "%s://%s%s%s#%s" % (splits.scheme, splits.hostname,
                                       port, splits.path,
                                       splits.fragment)
    else:
        root_uri = "%s://%s%s%s" % (splits.scheme, splits.hostname,
                                    port, splits.path)
    return splits.username, splits.password, root_uri
