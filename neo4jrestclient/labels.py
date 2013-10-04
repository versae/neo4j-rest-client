import json

from . import options
from .iterable import Iterable
from .request import Request, StatusException
from .utils import smart_quote


class Label(object):

    def __init__(self, label, auth=None, cypher=None):
        self._label = label
        self._auth = auth
        self._cypher = cypher

    def __eq__(self, obj):
        try:
            return obj._label == self._label
        except AttributeError:
            return obj == self._label

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return unicode.__repr__(unicode(self._label))


class LabelsProxy(object):
    """
    Class proxy for labels the GraphDatabase object.
    """

    def __init__(self, url, labels=None, auth=None, cypher=None, node=None):
        self._url = url
        self._labels = labels
        self._auth = auth or {}
        self._cypher = cypher
        self._node_cls = node
        if not labels:
            response, content = Request(**self._auth).get(self._url)
            if response.status == 200:
                results_list = json.loads(content)
                self._labels = [Label(label, auth=self._auth,
                                      cypher=self._cypher)
                                for label in results_list]
            else:
                msg = "Unable to read label(s)"
                try:
                    msg += ": " + json.loads(content).get('message')
                except (ValueError, AttributeError, KeyError):
                    pass
                raise StatusException(response.status, msg)
        else:
            self._labels = labels

    def __getitem__(self, key, tx=None, **kwargs):
        data = u""
        if kwargs:
            data = []
            for k, v in kwargs.iteritems():
                data.append("{}={}".format(smart_quote(k),
                                           smart_quote(v)))
            data = u"?{}".format(u"&".join(data))
        url = self._url.replace(u"labels",
                                u"label/{}/nodes{}".format(smart_quote(key),
                                                           data))
        response, content = Request(**self._auth).get(url)
        if response.status == 200:
            results_list = json.loads(content)
            if not results_list:
                return []
            elif isinstance(results_list, (tuple, list)):
                return Iterable(self._node_cls, results_list, "self",
                                auth=self._auth)
        else:
            msg = "Unable to read label(s)"
            try:
                msg += ": " + json.loads(content).get('message')
            except (ValueError, AttributeError, KeyError):
                pass
            raise StatusException(response.status, msg)

    def get(self, label, tx=None, **kwargs):
        return self.__getitem__(label, tx=tx, **kwargs)

    def __len__(self):
        return len(self._labels)

    def __contains__(self, key):
        try:
            return key._label in self._labels
        except AttributeError:
            return key in self._labels

    def __iter__(self):
        return iter(self._labels)

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return unicode(self._labels)


class NodeLabelsProxy(list):
    """
    Class proxy for node labels.
    """

    def __init__(self, url, labels=None, auth=None, cypher=None, node=None):
        self._url = url
        self._labels = labels
        self._auth = auth or {}
        self._cypher = cypher
        self._node_cls = node
        if self._labels:
            labels = []
            for label in self._labels:
                if isinstance(label, Label):
                    labels.append(label)
                else:
                    labels.append(Label(label, auth=self._auth,
                                        cypher=self._cypher))
            self._labels = labels
        if not self._labels:
            self._labels = self._update_labels()

    def __getitem__(self, key):
        return self._labels[key - 1]

    def __len__(self):
        return len(self._labels)

    def __contains__(self, key):
        try:
            return key._label in self._labels
        except AttributeError:
            return key in self._labels

    def _update_labels(self):
        response, content = Request(**self._auth).get(self._url)
        if response.status == 200:
            results_list = json.loads(content)
            return [Label(label, auth=self._auth, cypher=self._cypher)
                    for label in results_list]
        else:
            msg = "Unable to get labels"
            try:
                msg += ": " + json.loads(content).get('message')
            except (ValueError, AttributeError, KeyError):
                pass
            raise StatusException(response.status, msg)

    def append(self, labels):
        is_list = False
        if isinstance(labels, (tuple, list)):
            labels = [smart_quote(l) for l in labels]
            is_list = True
        else:
            labels = smart_quote(labels)
        response, content = Request(**self._auth).post(self._url, data=labels)
        if response.status == 204:
            if is_list:
                for label in labels:
                    if Label(label) not in self._labels:
                        self._labels.append(Label(labels, auth=self._auth,
                                                  cypher=self._cypher))
            elif Label(labels) not in self._labels:
                self._labels.append(Label(labels, auth=self._auth,
                                          cypher=self._cypher))
        else:
            msg = "Unable to add label"
            try:
                msg += ": " + json.loads(content).get('message')
            except (ValueError, AttributeError, KeyError):
                pass
            raise StatusException(response.status, msg)

    def remove(self, label):
        url = "{}/{}".format(self._url, smart_quote(label))
        response, content = Request(**self._auth).delete(url)
        if response.status == 204:
            if Label(label) in self._labels:
                self._labels.remove(label)
        elif options.SMART_ERRORS:
            raise KeyError("'{}' not found".format(label))
        else:
            msg = "Unable to remove label"
            try:
                msg += ": " + json.loads(content).get('message')
            except (ValueError, AttributeError, KeyError):
                pass
            raise StatusException(response.status, msg)

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return unicode(self._labels)
