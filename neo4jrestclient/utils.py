# -*- coding: utf-8 -*-
import json
import sys
PYTHON_VERSION = sys.version_info
PY2 = sys.version_info[0] == 2

if PY2:
    import urllib
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
    from urllib.parse import quote, unquote
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
