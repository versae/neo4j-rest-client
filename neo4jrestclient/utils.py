import json
import urllib
import sys
PYTHON_VERSION = sys.version_info


if PYTHON_VERSION < (2, 7):
    def smart_quote(val):
        if isinstance(val, (bool, int, long)):
            return urllib.quote(json.dumps(val), safe="")
        elif isinstance(val, float):
            return unicode(val)
        else:
            try:
                safe_key = urllib.quote(val, safe="")
            except (KeyError, UnicodeEncodeError, UnicodeError):
                safe_key = urllib.quote(val.encode("utf8"), safe="")
            return safe_key
else:
    def smart_quote(val):
        if isinstance(val, (bool, int, float, long)):
            return urllib.quote(json.dumps(val), safe="")
        else:
            try:
                safe_key = urllib.quote(val, safe="")
            except (KeyError, UnicodeEncodeError, UnicodeError):
                safe_key = urllib.quote(val.encode("utf8"), safe="")
            return safe_key
