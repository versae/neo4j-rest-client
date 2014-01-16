# -*- coding: utf-8 -*-
import json

from neo4jrestclient import options
from neo4jrestclient.iterable import Iterable
from neo4jrestclient.request import Request
from neo4jrestclient.exceptions import StatusException
from neo4jrestclient.query import FilterSequence
from neo4jrestclient.utils import smart_quote, text_type


class Label(object):

    def __init__(self, url, label, auth=None, cypher=None, node=None):
        self._url = url
        self._label = label
        self._auth = auth
        self._cypher = cypher
        self._node_cls = node
        # Check URLs like http://localhost:7474/db/data/node/27530/labels
        url_split = self._url.rsplit("/", 3)
        if url_split[1] == 'node':
            self._url = u"{}/labels".format(url_split[0])

    def __eq__(self, obj):
        try:
            return obj._label == self._label
        except AttributeError:
            return text_type(obj) == self._label

    def __hash__(self):
        return self._label.__hash__()

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"<Neo4j {}: {}>".format(self.__class__.__name__,
                                        self._label.__repr__())

    def add(self, *nodes):
        for node in nodes:
            node.labels.add(self._label)

    def get(self, **kwargs):
        data = u""
        if kwargs:
            data = []
            for k, v in kwargs.items():
                data.append("{}={}".format(smart_quote(k),
                                           smart_quote(json.dumps(v))))
            data = u"?{}".format(u"&".join(data))
        url = self._url.replace(
            u"labels",
            u"label/{}/nodes{}".format(smart_quote(self._label), data))
        response = Request(**self._auth).get(url)
        if response.status_code == 200:
            results_list = response.json()
            if not results_list:
                return []
            elif isinstance(results_list, (tuple, list)):
                return Iterable(self._node_cls, results_list, "self",
                                auth=self._auth)
        else:
            msg = "Unable to read label(s)"
            try:
                msg += ": " + response.json().get('message')
            except (ValueError, AttributeError, KeyError):
                pass
            raise StatusException(response.status_code, msg)

    def all(self):
        return self.get()

    def single(self):
        return self.filter()[0]

    def filter(self, *lookups):
        if not isinstance(lookups, (list, tuple)):
            lookups = [lookups]
        match = u"(n:`{}`)".format(self._label.replace("`", "\\`"))
        returns = self._node_cls
        types = {
            "node": self._node_cls,
        }
        return FilterSequence(self._cypher, self._auth, start=None,
                              matches=[match], types=types, lookups=lookups,
                              returns=returns)


class BaseLabelsProxy(object):
    """
    Base class proxy for labels.
    """

    def __init__(self, url, labels=None, auth=None, cypher=None, node=None):
        self._url = url
        self._labels = labels
        self._auth = auth or {}
        self._cypher = cypher
        self._node_cls = node
        if self._labels:
            labels = set()
            for label in self._labels:
                if isinstance(label, Label):
                    labels.add(label)
                else:
                    labels.add(Label(self._url, label, auth=self._auth,
                                     cypher=self._cypher, node=self._node_cls))
            self._labels = labels
        if not self._labels:
            self._labels = self._update_labels()

    def _update_labels(self):
        response = Request(**self._auth).get(self._url)
        if response.status_code == 200:
            results_list = response.json()
            return set([Label(self._url, label, auth=self._auth,
                              cypher=self._cypher, node=self._node_cls)
                        for label in results_list])
        else:
            msg = "Unable to get labels"
            try:
                msg += ": " + response.json().get('message')
            except (ValueError, AttributeError, KeyError):
                pass
            raise StatusException(response.status_code, msg)

    def get(self, key, **kwargs):
        if not isinstance(key, Label):
            key = Label(self._url, key, auth=self._auth, cypher=self._cypher,
                        node=self._node_cls)
        if key in self._labels:
            return key
        elif "default" in kwargs:
            return kwargs["default"]
        else:
            raise KeyError(key._label)

    def __getitem__(self, key):
        return self.get(key)

    def __len__(self):
        return len(self._labels)

    def __iter__(self):
        return iter(self._labels)

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return text_type(self._labels)

    def __contains__(self, key):
        return key in self._labels

    def __eq__(self, obj):
        try:
            return obj._labels == self._labels
        except AttributeError:
            return set(obj) == self._labels

    def __or__(self, obj):
        try:
            return obj._labels | self._labels
        except AttributeError:
            return set(obj) | self._labels


class LabelsProxy(BaseLabelsProxy):
    """
    Class proxy for labels the GraphDatabase object.
    """

    def create(self, label):
        return Label(self._url, label, auth=self._auth, cypher=self._cypher,
                     node=self._node_cls)


class NodeLabelsProxy(BaseLabelsProxy):
    """
    Class proxy for node labels.
    """

    def add(self, labels):
        single = False
        if not isinstance(labels, (tuple, list)):
            labels = [labels]
            single = True
        response = Request(**self._auth).post(self._url, data=labels)
        added = set()
        if response.status_code == 204:
            for label in labels:
                _label = label
                if not isinstance(_label, Label):
                    _label = Label(self._url, label, auth=self._auth,
                                   cypher=self._cypher, node=self._node_cls)
                if _label not in self._labels:
                    self._labels.add(_label)
                    added.add(_label)
        else:
            msg = "Unable to add label"
            try:
                msg += ": " + response.json().get('message')
            except (ValueError, AttributeError, KeyError):
                pass
            raise StatusException(response.status_code, msg)
        if single:
            return added.pop()
        else:
            return added

    def remove(self, label):
        self._discard(label, return_label=False, raise_error=True)

    def discard(self, label):
        self._discard(label, return_label=False, raise_error=False)

    def pop(self, label=None):
        return self._discard(label, return_label=True, raise_error=True)

    def clear(self):
        for label in self._labels:
            self._discard(label, return_label=False, raise_error=False)

    def _discard(self, label=None, return_label=False, raise_error=False):
        if not label:
            label = self._labels.pop()
        url = "{}/{}".format(self._url, smart_quote(label))
        response = Request(**self._auth).delete(url)
        if response.status_code == 204:
            _label = label
            if not isinstance(_label, Label):
                _label = Label(self._url, label)
            if _label in self._labels:
                self._labels.remove(_label)
            if return_label:
                return _label
        elif raise_error:
            if options.SMART_ERRORS:
                raise KeyError("'{}' not found".format(_label))
            else:
                msg = "Unable to remove label"
                try:
                    msg += ": " + response.json().get('message')
                except (ValueError, AttributeError, KeyError):
                    pass
                raise StatusException(response.status_code, msg)
