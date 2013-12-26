# -*- coding: utf-8 -*-
import json

from neo4jrestclient import options
from neo4jrestclient.iterable import Iterable
from neo4jrestclient.request import Request, StatusException
from neo4jrestclient.utils import smart_quote, text_type


class Label(object):

    def __init__(self, label, auth=None, cypher=None):
        self._label = label
        self._auth = auth
        self._cypher = cypher

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
        return '"{}"'.format(text_type(self._label))


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
            response = Request(**self._auth).get(self._url)
            if response.status_code == 200:
                results_list = response.json()
                self._labels = [Label(label, auth=self._auth,
                                      cypher=self._cypher)
                                for label in results_list]
            else:
                msg = "Unable to read label(s)"
                try:
                    msg += ": " + response.json().get('message')
                except (ValueError, AttributeError, KeyError):
                    pass
                raise StatusException(response.status_code, msg)
        else:
            self._labels = labels

    def __getitem__(self, key, tx=None, **kwargs):
        data = u""
        if kwargs:
            data = []
            for k, v in kwargs.items():
                data.append("{}={}".format(smart_quote(k),
                                           smart_quote(json.dumps(v))))
            data = u"?{}".format(u"&".join(data))
        url = self._url.replace(u"labels",
                                u"label/{}/nodes{}".format(smart_quote(key),
                                                           data))
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
        return text_type(self._labels)


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
            labels = set()
            for label in self._labels:
                if isinstance(label, Label):
                    labels.add(label)
                else:
                    labels.add(Label(label, auth=self._auth,
                                     cypher=self._cypher))
            self._labels = labels
        if not self._labels:
            self._labels = self._update_labels()

    def __len__(self):
        return len(self._labels)

    def __contains__(self, key):
        try:
            return key._label in self._labels
        except AttributeError:
            return key in self._labels

    def __eq__(self, obj):
        try:
            return obj._labels == self._labels
        except AttributeError:
            return set(obj) == self._labels

    def _update_labels(self):
        response = Request(**self._auth).get(self._url)
        if response.status_code == 200:
            results_list = response.json()
            return set([Label(label, auth=self._auth, cypher=self._cypher)
                        for label in results_list])
        else:
            msg = "Unable to get labels"
            try:
                msg += ": " + response.json().get('message')
            except (ValueError, AttributeError, KeyError):
                pass
            raise StatusException(response.status_code, msg)

    def add(self, labels):
        if not isinstance(labels, (tuple, list)):
            labels = [labels]
        response = Request(**self._auth).post(self._url, data=labels)
        if response.status_code == 204:
            for label in labels:
                _label = Label(label, auth=self._auth, cypher=self._cypher)
                if _label not in self._labels:
                    self._labels.add(_label)
        else:
            msg = "Unable to add label"
            try:
                msg += ": " + response.json().get('message')
            except (ValueError, AttributeError, KeyError):
                pass
            raise StatusException(response.status_code, msg)

    def remove(self, label):
        url = "{}/{}".format(self._url, smart_quote(label))
        response = Request(**self._auth).delete(url)
        if response.status_code == 204:
            if Label(label) in self._labels:
                self._labels.remove(label)
        elif options.SMART_ERRORS:
            raise KeyError("'{}' not found".format(label))
        else:
            msg = "Unable to remove label"
            try:
                msg += ": " + response.json().get('message')
            except (ValueError, AttributeError, KeyError):
                pass
            raise StatusException(response.status_code, msg)

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return text_type(self._labels)
