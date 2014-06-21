# -*- coding: utf-8 -*-
from datetime import date, datetime, time
try:
    import cPickle as pickle
except:
    import pickle
import weakref
import warnings
from lucenequerybuilder import Q

from neo4jrestclient import options
from neo4jrestclient.constants import (
    BREADTH_FIRST, DEPTH_FIRST,
    STOP_AT_END_OF_GRAPH,
    NODE_GLOBAL, NODE_PATH, NODE_RECENT,
    RELATIONSHIP_GLOBAL, RELATIONSHIP_PATH,
    RELATIONSHIP_RECENT, NONE, INDEX, ITERABLE,
    NODE, RELATIONSHIP, PATH, POSITION, FULLPATH, RAW,
    INDEX_FULLTEXT, TX_GET, TX_PUT, TX_POST, TX_DELETE,
    INDEX_RELATIONSHIP, INDEX_NODE,
    RELATIONSHIPS_ALL, RELATIONSHIPS_IN, RELATIONSHIPS_OUT,
    RETURN_ALL_NODES, RETURN_ALL_BUT_START_NODE
)
from neo4jrestclient.iterable import Iterable
from neo4jrestclient.labels import NodeLabelsProxy, LabelsProxy
from neo4jrestclient.query import (
    QuerySequence, FilterSequence, QueryTransaction, CypherException
)
from neo4jrestclient.request import Request
from neo4jrestclient.exceptions import (NotFoundError, StatusException,
                                        TransactionException)
from neo4jrestclient.traversals import TraversalDescription, GraphTraversal
from neo4jrestclient.utils import (PY2, text_type, smart_quote, string_types,
                                   unquote, get_auth_from_uri)

__all__ = ["GraphDatabase", "Incoming", "Outgoing", "Undirected",
           "StopAtDepth", "NotFoundError", "StatusException", "Q"]


class StopAtDepth(object):
    """
    Only traverse to a certain depth.
    """

    def __init__(self, depth):
        self.depth = depth

    def __get__(self):
        return self.depth


class GraphDatabase(object):
    """
    Main class for connection to Ne4j standalone REST server.
    """

    def __init__(self, url, username=None, password=None, cert_file=None,
                 key_file=None):
        username_uri, password_uri, xxx = get_auth_from_uri(url)
        username = username or username_uri
        password = password or password_uri
        self._auth = {
            "username": username,
            "password": password,
            "cert_file": cert_file,
            "key_file": key_file,
        }
        self._transactions = {}
        self.url = None
        if url.endswith("/"):
            self.url = url
        else:
            self.url = "%s/" % url
        response = Request(**self._auth).get(self.url)
        if response.status_code == 200:
            response_json = response.json()
        else:
            raise NotFoundError(response.status_code, "Unable get root")
        if "data" in response_json and "management" in response_json:
            response = Request(**self._auth).get(response_json["data"])
            if response.status_code == 200:
                response_json = response.json()
            else:
                raise NotFoundError(response.status_code, "Unable get root")
        if response_json:
            self._relationship_index = response_json['relationship_index']
            self._node = response_json['node']
            self._labels = response_json.get('labels',
                                             "{}labels".format(self.url))
            self._labels_list = None
            self._node_index = response_json['node_index']
            self._reference_node = response_json.get('reference_node', None)
            self._extensions_info = response_json['extensions_info']
            self._extensions = response_json['extensions']
            self._cypher = response_json.get('cypher', None)
            self._transaction = response_json.get('transaction', None)
            self.VERSION = response_json.get('neo4j_version', None)
            if self.VERSION:
                self._auth.update({'version': self.VERSION})
            self._extensions_cache = None
            self.nodes = NodesProxy(self._node, self._reference_node,
                                    self._node_index,
                                    auth=self._auth, cypher=self._cypher)
            # Backward compatibility. The current style is more pythonic
            self.node = self.nodes
            # HACK: Neo4j doesn't provide the URLs to access to relationships
            url_parts = self._node.rpartition("node")
            self._relationship = "%s%s%s" % (url_parts[0], RELATIONSHIP,
                                             url_parts[2])
            self.relationships = RelationshipsProxy(self._relationship,
                                                    self._relationship_index,
                                                    auth=self._auth,
                                                    cypher=self._cypher)
            self.Traversal = GraphTraversal
            try:
                self._batch = response_json["batch"]
            except KeyError:
                self._batch = "%sbatch" % self.url

    def __eq__(self, obj):
        return (
            self._relationship_index == obj._relationship_index
            and self._relationship == obj._relationship
            and self._node == obj._node
            and self._labels == obj._labels
            and self._labels_list == obj._labels_list
            and self._node_index == obj._node_index
            and self._reference_node == obj._reference_node
            and self._extensions_info == obj._extensions_info
            and self._extensions == obj._extensions
            and self._cypher == obj._cypher
            and self._transaction == obj._transaction
            and self._batch == obj._batch
        )

    def _get_extensions(self):
        if not self._extensions_cache:
            self._extensions_cache = ExtensionsProxy(self._extensions,
                                                     auth=self._auth,
                                                     cypher=self._cypher)
        return self._extensions_cache
    extensions = property(_get_extensions)

    def _get_reference_node(self):
        warnings.warn("Deprecated, the reference node is not needed anymore",
                      DeprecationWarning)
        if self._reference_node:
            return Node(self._reference_node)
        else:
            return None
    reference_node = property(_get_reference_node)

    def flush(self, return_globals=True):
        if options.TX_NAME in globals():
            del globals()[options.TX_NAME]
        self._transactions = {}
        if return_globals:
            return globals()

    def traverse(self, start_node, *args, **kwargs):
        return start_node.traverse(*args, **kwargs)

    def traversal(self):
        return TraversalDescription(auth=self._auth, cypher=self._cypher)

    def transaction(self, using_globals=True, commit=True, update=True,
                    transaction_id=None, context=None, for_query=False,
                    rollback=True, execute=False):
        if transaction_id not in self._transactions:
            transaction_id = len(self._transactions.keys())
        if for_query:
            types = {
                "node": Node,
                "relationship": Relationship,
                "path": Path,
                "position": Position,
            }
            tx = QueryTransaction(self, transaction_id, rollback=rollback,
                                  commit=commit, update=update, types=types,
                                  execute=execute)
        else:
            tx = Transaction(self, transaction_id, context or {},
                             commit=commit, update=update)
        self._transactions[transaction_id] = tx
        if using_globals:
            globals()[options.TX_NAME] = self._transactions[transaction_id]
        return self._transactions[transaction_id]

    def query(self, q, params=None, returns=RAW, tx=None):
        if self._cypher or self._transaction:
            types = {
                "node": Node,
                "relationship": Relationship,
                "path": Path,
                "position": Position,
            }
            tx = Transaction.get_transaction(tx)
            # The non transactional Cypher endpoint will be removed eventually,
            # So we create always a transaction per query for Neo4j 2.0+
            if (tx is None
                    and self.VERSION and self.VERSION.split(".")[0] >= "2"):
                tx = self.transaction(for_query=True, execute=True,
                                      using_globals=False)
            return QuerySequence(self._cypher, self._auth, q=q, params=params,
                                 types=types, returns=returns, tx=tx)
        else:
            raise CypherException

    def _get_labels(self):
        if not self._labels_list and self.VERSION.split(".")[0] >= "2":
            self._labels_list = LabelsProxy(self._labels,
                                            auth=self._auth,
                                            cypher=self._cypher,
                                            node=Node)
        return self._labels_list
    labels = property(_get_labels)


class TransactionOperationProxy(dict, object):
    """
    TransactionOperationProxy class. A proxy to convert transaction operations
    into final instances of Node or Relationship.
    """

    def __init__(self, obj=None, job=None, typ=None, **kwargs):
        self._proxy = None
        if obj is not None:
            self._object_ref = weakref.ref(obj)
        else:
            self._object_ref = None
        self._job_id = job
        if "body" not in kwargs:
            if typ == NODE:
                kwargs.update({"body": {}})
            else:  # RELATIONSHIP and INDEX
                kwargs.update({"body": {"data": {}}})
        elif typ == RELATIONSHIP and "data" not in kwargs["body"]:
            kwargs["body"].update({"data": {}})
        self._extras = {"type": typ}
        super(TransactionOperationProxy, self).__init__(kwargs)

    def __call__(self):
        return dict(self)

    def __getattribute__(self, attr, *args, **kwargs):
        _proxy = object.__getattribute__(self, "_proxy")
        _type = object.__getattribute__(self, "_extras")["type"]
        if _proxy is not None:
            return getattr(_proxy, attr)
        elif _type and attr in ("relationships", "start", "end", "type", "id"):
            if (_type == NODE and attr == "relationships"
                    or _type == RELATIONSHIP
                    and attr in ("start", "end", "type")):
                return object.__getattribute__(self, "_get_%s" % attr)()
            else:
                return object.__getattribute__(self, attr)
        elif _type == NODE:
            try:
                return object.__getattribute__(self, attr)
            except AttributeError:
                warnings.warn("Deprecated, in favor of pythonic style to "
                              "declare relationships: "
                              "n2.relationships.create(rel_name, n2). "
                              "This is needed in order to handle pickling in "
                              "nodes.",
                              DeprecationWarning)

                def _create_relationship(*args, **kwargs):
                    _attr = "_create_relationship"
                    _func = object.__getattribute__(self, _attr)
                    _relationship = _func(attr)
                    return _relationship(*args, **kwargs)

                return _create_relationship
        else:
            return object.__getattribute__(self, attr)

    def __setattribute__(self, attr, val):
        _proxy = object.__getattribute__(self, "_proxy")
        if _proxy is not None:
            setattr(_proxy, attr, val)
        else:
            object.__setattr__(self, attr, val)

    def set(self, key, value):
        self.__setitem__(key, value)

    def get(self, key):
        self.__getitem__(key)

    def _get_properties(self):
        return dict(self)

    def _set_properties(self, props={}):
        # _type = object.__getattribute__(self, "_extras")["type"]
        if type == RELATIONSHIP:
            _body = dict.__getitem__(self, "body")
            _data = dict.__getitem__(_body, "data")
            _data.update(props)
        else:
            _body = dict.__getitem__(self, "body")
            _body.update(props)

    def _del_properties(self):
        # _type = object.__getattribute__(self, "_extras")["type"]
        if type == RELATIONSHIP:
            _body = dict.__getitem__(self, "body")
            dict.__setitem__(_body, "data", {})
        else:
            dict.__setitem__(self, "body", {})

    properties = property(_get_properties, _set_properties, _del_properties)

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        attr = "__unicode__"
        try:
            return getattr(object.__getattribute__(self, "_proxy"), attr)()
        except AttributeError:
            pass
        return object.__repr__(self)

    def __getitem__(self, key):
        _type = object.__getattribute__(self, "_extras")["type"]
        _proxy = object.__getattribute__(self, "_proxy")
        if _proxy is not None:
            if isinstance(key, slice):
                eltos = _proxy._list[key]
                if _proxy._attribute:
                    return [_proxy._class(elto[_proxy._attribute],
                                          update_dict=elto) for elto in eltos]
                else:
                    return [_proxy._class(elto) for elto in eltos]
            else:
                return _proxy.__getitem__(key)
        else:
            if _type == RELATIONSHIP:
                _body = dict.__getitem__(self, "body")
                return dict.__getitem__(_body, key)
            elif _type == ITERABLE:
                _body = dict.__getitem__(self, "body")
                dict.__setitem__(self, "key", key)
                return self
            else:
                _body = dict.__getitem__(self, "body")
                return dict.__getitem__(_body, key)

    def __setitem__(self, key, val):
        _type = object.__getattribute__(self, "_extras")["type"]
        _proxy = object.__getattribute__(self, "_proxy")
        if _proxy is not None:
            return _proxy.__setitem__(key, val)
        else:
            if _type == RELATIONSHIP:
                _body = dict.__getitem__(self, "body")
                _data = dict.__getitem__(_body, "data")
                return dict.__setitem__(_data, key, val)
            else:
                _body = dict.__getitem__(self, "body")
                return dict.__setitem__(_body, key, val)

    def get_object(self):
        if self._object_ref:
            return self._object_ref()
        else:
            return None

    def get_job_id(self):
        return self._job_id

    def change(self, cls, url, data=None, auth=None):
        _auth = auth or {}
        _type = object.__getattribute__(self, "_extras")["type"]
        if _type in (INDEX_NODE, INDEX_RELATIONSHIP):
            # TODO: Improve the way we get the name of the index,
            #       maybe including the name in the results
            name = data["location"].split(data["from"])[1][1:-1]
            if NODE in data["from"]:
                self._proxy = cls(index_for=NODE, name=name, auth=_auth,
                                  **data["body"])
            else:
                self._proxy = cls(index_for=RELATIONSHIP,
                                  name=name, auth=_auth,
                                  **data["body"])
        elif _type == ITERABLE:
            if not data["body"] or len(data["body"]) == 0:
                self._proxy = list()
            else:
                self_keys = self().keys()
                # Check if it is an element from the iterable
                if "key" in self_keys and "of" in self_keys:
                    _key = dict.__getitem__(self, "key")
                    _of = dict.__getitem__(self, "of")
                    _body = data["body"][_key]
                    if _of == NODE:
                        cls = Node
                    else:  # Relationship
                        cls = Relationship
                    self._proxy = cls(_body["self"],
                                      update_dict=_body, auth=_auth)
                else:
                    first_element = data["body"][0]
                    if "self" in first_element:
                        if NODE in first_element["self"]:
                            self._proxy = cls(Node, data["body"], "self",
                                              auth=_auth)
                        elif RELATIONSHIP in first_element["self"]:
                            self._proxy = cls(Relationship, data["body"],
                                              "self", auth=_auth)
                    else:
                        self._proxy = cls(Path, data["body"], auth=_auth)
        else:
            if "self" in data["body"] and data["body"]["self"] != url:
                self._proxy = cls(data["body"]["self"],
                                  update_dict=data["body"], auth=_auth)
            elif data["body"] == data["returns"]:
                # Basic types likes strings or integers
                self._proxy = cls(data["body"])
            else:
                self._proxy = cls(url, update_dict=data["body"], auth=_auth)

    # Common functions
    def _get_id(self):
        _body = dict.__getitem__(self, "body")
        return "{%s}" % _body["id"]

    # Node functions
    def _get_relationships(self):
        """
        HACK: Return a 3-methods class: incoming, outgoing and all.
        """
        return Relationships(self)

    def _create_relationship(self, relationship_name, *args, **kwargs):
        _job_id = object.__getattribute__(self, "_job_id")

        def relationship(to, *args, **kwargs):
            tx = Transaction.get_transaction(kwargs.get("tx", None))
            object.__getattribute__(self, "_extras")["to"] = to
            create_relationship_url = "{%s}/relationships" % _job_id
            # Check if target node doesn't exist yet
            if (isinstance(to, TransactionOperationProxy)
                    and not isinstance(to, Node)):
                to_url = "{%s}" % to()["id"]
            else:
                to_url = to.url
            data = {
                "to": to_url,
                "type": relationship_name,
            }
            if "tx" in kwargs and isinstance(kwargs["tx"], Transaction):
                x = kwargs.pop("tx", None)
                del x  # Makes pyflakes happy
            if kwargs:
                data.update({"data": kwargs})
            object.__getattribute__(self, "_extras")["tx"] = tx
            return tx.append(TX_POST, create_relationship_url,
                             data=data, obj=self, returns=RELATIONSHIP)
        return relationship

    # Relationships functions
    def _get_start(self):
        _proxy = object.__getattribute__(self, "_proxy")
        node_from_string = dict.__getitem__(_proxy, "to")
        node_from_index = int(node_from_string.split("/")[0][1:-1])
        tx = object.__getattribute__(self, "_extras")["tx"]
        node_from = tx.operations[node_from_index]
        return node_from

    def _get_end(self):
        node_to = object.__getattribute__(self, "_extras")["to"]
        return node_to

    def _get_type(self):
        _body = dict.__getitem__(self, "body")
        _data = dict.__getitem__(_body, "data")
        return dict.__getitem__(_data, "type")

    # Index functions
    def add(self, key, value, item, tx=None):
        _body = dict.__getitem__(self, "body")
        _name = dict.__getitem__(_body, "name")
        _type = object.__getattribute__(self, "_extras")["type"]
        if _type == INDEX_NODE:
            index_for = NODE
        else:
            index_for = RELATIONSHIP

        if isinstance(value, (list, tuple)):
            tx = tx or value[1]
            value = value[0]
        if isinstance(item, Transaction):
            tx = tx or item
            item = item.get_value()
        tx = Transaction.get_transaction(tx)
        # Neo4j hardly crush if you try to index a relationship in a
        # node index and viceversa.
        is_node_index = (index_for == NODE
                         and isinstance(item, Node))
        is_relationship_index = (index_for == RELATIONSHIP
                                 and isinstance(item, Relationship))
        if not (is_node_index or is_relationship_index
                or TransactionOperationProxy):
            raise TypeError("%s is a %s and the index is for %ss"
                            % (item, index_for.capitalize(), index_for))
        if isinstance(item, Base):
            url_ref = item.url
        elif isinstance(item, TransactionOperationProxy):
            url_ref = "{%s}" % item()["id"]
        else:
            url_ref = item
        data = {"key": key,
                "value": value,  # smart_quote is not needed anymore
                "uri": url_ref}
        if tx:
            request_url = "index/%s/%s" % (index_for, _name)
            op = tx.append(TX_POST, request_url, data=data,
                           obj=self, returns=index_for)
            return op


class Transaction(object):
    """
    Transaction class.
    """

    def __init__(self, cls, transaction_id, context, commit=True, update=True):
        self._class = cls
        self.url = self._class._batch
        self.id = transaction_id
        self.context = context
        self.auto_commit = commit
        self.auto_update = update
        self.operations = []
        self.references = []
        self._value = None
        self._attribute = None

    def __call__(self, value):
        """
        Call method in order to allow expresions like

            with gdb.transaction(using_globals=False) as tx:
                n[key] = tx(value)
        """
        self._value = value
        return self

    def get_value(self):
        return self._value

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.auto_commit:
            return self.commit(type, value, traceback)
        return True

    def _results_list_to_dict(self, results):
        result_dict = {}
        for result in results:
            result_id = result.pop("id")
            if "body" in result and "self" in result["body"]:
                if NODE in result["body"]["self"]:
                    result["returns"] = Node
                elif RELATIONSHIP in result["body"]["self"]:
                    result["returns"] = Relationship
            elif "body" in result and isinstance(result["body"],
                                                 (tuple, list)):
                result["returns"] = Iterable
            elif "from" in result and INDEX in result["from"]:
                result["returns"] = Index
            elif "body" in result:
                result["returns"] = result["body"]
            else:
                result["returns"] = None
            if "returns" in result:
                result_dict[result_id] = result
        return result_dict

    def _batch(self):
        request = Request(**self._class._auth)
        response = request.post(self.url, data=self.operations)
        if response.status_code == 200:
            results_list = response.json()
            results_dict = self._results_list_to_dict(results_list)
            return results_dict
        else:
            raise TransactionException(response.status_code)

    def commit(self, *args, **kwargs):
        auth = self._class._auth
        self._class.flush()
        results = self._batch()
        # Objects to update
        if self.auto_update:
            for operation in self.operations:
                on_object = operation.get_object()
                if hasattr(on_object, "update"):
                    on_object.update(extensions=False,
                                     delete_on_not_found=True)
        # Objects to return
        for referenced_object in self.references:
                ref_object = referenced_object()
                result = results[ref_object()["id"]]
                if "returns" in result:
                    if "location" in result:
                        cls = result["returns"]
                        url = result["location"]
                    elif "body" in result:
                        cls = result["returns"]
                        if "self" in result["body"]:
                            url = result["body"]["self"]
                        elif isinstance(result["body"], (tuple, list)):
                            url = None
                            ref_object.change(cls, url, data=result, auth=auth)
                        elif result["body"] == result["returns"]:
                            url = None
                            ref_object.change(cls.__class__, cls, data=result,
                                              auth=auth)
                    if cls and url:
                        ref_object.change(cls, url, data=result, auth=auth)
        self.references = []
        self.operations = []
        # Destroy the object after commit
        self = None
        if "type" in kwargs and isinstance(kwargs["type"], Exception):
            raise kwargs["type"]
        else:
            return True

    def append(self, method, url, data=None, obj=None, returns=None, of=None):
        job_id = len(self.operations)
        if url.startswith("{"):
            url_to = url
        elif not url.startswith("/"):
            url_to = "/%s" % url.replace(self._class.url, "")
        else:
            url_to = url
        params = {
            "method": method,
            "to": url_to,
            "id": job_id,
            "of": of,
        }
        if data:
            params.update({"body": data})
        # Reunify PUT methods in just one
        transaction_operation = None
        if method == TX_PUT:
            # TODO: Improve the performance of this search
            for i, operation in enumerate(self.operations):
                if (operation()["method"] == params["method"] == TX_PUT
                        and operation()["to"] == params["to"]):
                    if "body" in operation():
                        self.operations[i]()["body"].update(params["body"])
                    else:
                        self.operations[i]()["body"] = params["body"]
                    transaction_operation = operation
                    break
        if not transaction_operation:
            transaction_operation = TransactionOperationProxy(obj=obj,
                                                              job=job_id,
                                                              typ=returns,
                                                              **params)
            self.operations.append(transaction_operation)
            if method in (TX_POST, TX_GET):
                self.references.append(weakref.ref(transaction_operation))
        return transaction_operation

    @staticmethod
    def get_transaction(tx=None):
        if not tx and options.TX_NAME in globals():
            return globals()[options.TX_NAME]
        elif isinstance(tx, (Transaction, QueryTransaction)):
            return tx
        elif (isinstance(tx, (list, tuple)) and len(tx) > 1
              and isinstance(tx[-1], (Transaction, QueryTransaction))):
            return tx[-1]
        else:
            return None


class Base(object):
    """
    Base class.
    """

    def __init__(self, url, create=False, data={}, update_dict={}, auth=None,
                 cypher=None):
        self._dic = {}
        self._auth = auth or {}
        self._cypher = cypher
        self.url = None
        self._labels = None
        # Allow update an object using only a new data dict of properties
        self._update_dict = update_dict
        if url.endswith("/"):
            url = url[:-1]
        if create:
            response = Request(**self._auth).post(url, data=data)
            if response.status_code == 201:
                self._dic.update(data.copy())
                self._update_dict_data()
                self.url = response.headers.get(
                    "location",
                    response.headers.get("content-location")
                )
            else:
                raise NotFoundError(response.status_code, "Invalid data sent")
        if not self.url:
            self.url = url
        self.update()

    def _update_dict_data(self):
        if "data" in self._dic:
            self._dic["data"] = dict((Base._safe_string(k),
                                      Base._safe_string(v))
                                     for k, v in self._dic["data"].items())

    @staticmethod
    def _safe_string(s):
        if options.SMART_DATES:
            if isinstance(s, (datetime, date, time)):
                return s
            else:
                try:
                    dt = datetime.strptime(s, options.DATETIME_FORMAT)
                except ValueError:
                    for date_type in ["date", "time"]:
                        try:
                            option = "%s_FORMAT" % date_type.upper()
                            format = getattr(options, option)
                            t = getattr(datetime.strptime(s, format),
                                        date_type)()
                        except ValueError:
                            pass
                        else:
                            return t
                else:
                    return dt
        if isinstance(s, text_type):
            return s
        if isinstance(s, string_types):
            if PY2:
                return text_type(s.decode("utf-8"))
            else:
                return text_type(s)
        else:
            # We avoid convert non-string values
            return s

    def update(self, extensions=True, delete_on_not_found=False):
        if self._update_dict:
            update_dict = self._update_dict
            status = 200
        else:
            response = Request(**self._auth).get(self.url)
            update_dict = response.json().copy()
            status = response.status_code
        if status == 200:
            self._dic.update(update_dict)
            if extensions:
                self._extensions = self._dic.get('extensions', {})
                if self._extensions:
                    self.extensions = ExtensionsProxy(self._extensions,
                                                      auth=self._auth)
            self._update_dict = {}
        elif delete_on_not_found and status == 404:
            self.url = None
            self._dic = {}
            self = None
            del self
        else:
            raise NotFoundError(response.status_code, "Unable get object")

    def delete(self, key=None, tx=None):
        if key:
            return self.__delitem__(key, tx=tx)
        tx = Transaction.get_transaction(tx)
        if tx:
            return tx.append(TX_DELETE, self.url, obj=self)
        response = Request(**self._auth).delete(self.url)
        if response.status_code == 204:
            self.url = None
            self._dic = None
            self = None
            del self
        elif response.status_code == 404:
            raise NotFoundError(response.status_code,
                                "Node or property not found")
        else:
            raise StatusException(response.status_code,
                                  "Node could not be deleted (still has "
                                  "relationships?)")

    def __getitem__(self, key, tx=None):
        property_url = self._dic["property"].replace("{key}", smart_quote(key))
        tx = Transaction.get_transaction(tx)
        if tx:
            if isinstance(tx, QueryTransaction):
                return self._dic["data"][key]
            else:
                return tx.append(TX_GET, property_url, obj=self)
        response = Request(**self._auth).get(property_url)
        if response.status_code == 200:
            self._dic["data"][key] = response.json()
        else:
            if options.SMART_ERRORS:
                raise KeyError()
            else:
                raise NotFoundError(response.status_code,
                                    "Node or propery not found")
        if options.SMART_DATES:
            return Base._safe_string(self._dic["data"][key])
        else:
            return self._dic["data"][key]

    def get(self, key, *args, **kwargs):
        tx = kwargs.get("tx", None)
        try:
            return self.__getitem__(key, tx=tx)
        except (KeyError, NotFoundError, StatusException):
            if args:
                return args[0]
            elif "default" in kwargs:
                return kwargs["default"]
            elif options.SMART_ERRORS:
                raise KeyError(key)
            else:
                raise NotFoundError()

    def __contains__(self, obj):
        return obj in self._dic["data"]

    def __setitem__(self, key, value, tx=None):
        if value is None:
            self._dic["data"].update({key: value})
        else:
            if isinstance(key, (list, tuple)):
                tx = tx or key[1]
                key = key[0]
            if isinstance(value, Transaction):
                tx = tx or value
                value = value.get_value()
            property_url = self._dic["property"].replace("{key}",
                                                         smart_quote(key))
            tx = Transaction.get_transaction(tx)
            if tx:
                transaction_url = self._dic["property"].replace("{key}", "")
                return tx.append(TX_PUT, transaction_url, {key: value},
                                 obj=self)
            response = Request(**self._auth).put(property_url, data=value)
            if response.status_code == 204:
                if options.SMART_DATES:
                    self._dic["data"].update({key: Base._safe_string(value)})
                else:
                    self._dic["data"].update({key: value})
            elif response.status_code == 404:
                raise NotFoundError(response.status_code,
                                    "Node or property not found")
            else:
                msg = "Invalid data sent"
                try:
                    msg += ": " + response.json().get('message')
                except (ValueError, AttributeError, KeyError):
                    pass
                raise StatusException(response.status_code, msg)

    def set(self, key, value, tx=None):
        tx = Transaction.get_transaction(tx)
        if tx:
            return self.__setitem__(key, value, tx=tx)
        self.__setitem__(key, value)

    def __delitem__(self, key, tx=None):
        property_url = self._dic["property"].replace("{key}", smart_quote(key))
        tx = Transaction.get_transaction(tx)
        if tx:
            return tx.append(TX_DELETE, property_url, obj=self)
        response = Request(**self._auth).delete(property_url)
        if response.status_code == 204:
            del self._dic["data"][key]
        elif response.status_code == 404:
            if options.SMART_ERRORS:
                raise KeyError()
            else:
                raise NotFoundError(response.status_code,
                                    "Node or property not found")
        else:
            raise StatusException(response.status_code,
                                  "Node or property not found")

    def __len__(self):
        # This functions allows to eval nodes in "if" statements
        if "data" and self._dic:
            return len(self._dic["data"])
        else:
            return 0

    def __iter__(self):
        return self._dic["data"].__iter__()

    def __lt__(self, other):
        return (self.url < other.url)

    def __eq__(self, obj):
        if not self.url and not self._dic:
            return (obj is None)
        else:
            return (hasattr(obj, "url")
                    and self.url == obj.url
                    and hasattr(obj, "__class__")
                    and self.__class__ == obj.__class__)

    def __ne__(self, obj):
        if not self.url and not self._dic:
            return not (obj is None)
        else:
            return not (hasattr(obj, "url")
                        and self.url == obj.url
                        and hasattr(obj, "__class__")
                        and self.__class__ == obj.__class__)

    def __nonzero__(self):
        return bool(self._dic)

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        if not self.url and not self._dic:
            return None
        else:
            return u"<Neo4j %s: %s>" % (self.__class__.__name__, self.url)

    def _get_properties(self):
        if options.SMART_DATES:
            self._update_dict_data()
        return self._dic["data"]

    def _set_properties(self, props={}):
        if not props:
            return None
        properties_url = self._dic["properties"]
        response = Request(**self._auth).put(properties_url, data=props)
        if response.status_code == 204:
            self._dic["data"] = props.copy()
            self._update_dict_data()
            return props
        elif response.status_code == 400:
            msg = "Invalid data sent"
            try:
                msg += ": " + response.json().get('message')
            except (ValueError, AttributeError, KeyError):
                pass
            raise StatusException(response.status_code, msg)
        else:
            raise NotFoundError(response.status_code, "Properties not found")

    def _del_properties(self):
        properties_url = self._dic["properties"]
        response = Request(**self._auth).delete(properties_url)
        if response.status_code == 204:
            self._dic["data"] = {}
        else:
            raise NotFoundError(response.status_code, "Properties not found")
    # TODO: Create an own Property class to handle transactions
    properties = property(_get_properties, _set_properties, _del_properties)


class NodesProxy(dict):
    """
    Class proxy for node in order to allow get a node by id and
    create new nodes through calling.
    """

    def __init__(self, node, reference_node=None, node_index=None, auth=None,
                 cypher=None):
        self._node = node
        self._reference_node = reference_node
        self._node_index = node_index
        self._auth = auth or {}
        self._cypher = cypher

    def __call__(self, **kwargs):
        tx = Transaction.get_transaction(kwargs.get("tx", None))
        reference = kwargs.pop("reference", False)
        if reference and self._reference_node:
            return self.__getitem__(self._reference_node, tx=tx)
        else:
            return self.create(**kwargs)

    def __getitem__(self, key, tx=None):
        tx = Transaction.get_transaction(tx)
        if tx:
            if isinstance(key, string_types) and key.startswith(self._node):
                return tx.append(TX_GET, key, obj=self)
            else:
                return tx.append(TX_GET, "%s/%s/" % (self._node, key),
                                 obj=self)
        else:
            if isinstance(key, string_types) and key.startswith(self._node):
                return Node(key, auth=self._auth, cypher=self._cypher)
            else:
                return Node("%s/%s/" % (self._node, key), auth=self._auth,
                            cypher=self._cypher)

    def get(self, key, *args, **kwargs):
        tx = Transaction.get_transaction(kwargs.get("tx", None))
        try:
            return self.__getitem__(key, tx=tx)
        except (KeyError, NotFoundError, StatusException):
            if args:
                return args[0]
            elif "default" in kwargs:
                return kwargs["default"]
            else:
                raise NotFoundError()

    def create(self, **kwargs):
        tx = Transaction.get_transaction(kwargs.get("tx", None))
        if tx:
            if "tx" in kwargs and isinstance(kwargs["tx"], Transaction):
                x = kwargs.pop("tx", None)
                del x  # Makes pyflakes happy
            op = tx.append(TX_POST, self._node, data=kwargs, obj=self,
                           returns=NODE)
            return op
        else:
            return Node(self._node, create=True, data=kwargs, auth=self._auth,
                        cypher=self._cypher)

    def delete(self, key, tx=None):
        tx = Transaction.get_transaction(tx)
        if tx:
            return self.__getitem__(key, tx=tx)
        else:
            node = self.__getitem__(key)
            del node

    def filter(self, lookups=[], start=None):
        return elements_filter(self, lookups=lookups, start=start,
                               returns=Node)

    def all(self):
        return self.filter()

    def _indexes(self):
        if self._node_index:
            return IndexesProxy(self._node_index, NODE, auth=self._auth,
                                cypher=self._cypher)
    indexes = property(_indexes)


class Node(Base):
    """
    Node class.
    """

    def __getattr__(self, *args, **kwargs):
        """
        HACK: Allow to set node relationship
        """
        warnings.warn("Deprecated, in favor of pythonic style to declare "
                      "relationships: n2.relationships.create(rel_name, n2). "
                      "This is needed in order to handle pickling in nodes.",
                      DeprecationWarning)
        return self._create_relationship(*args, **kwargs)

    def _create_relationship(self, relationship_name, *args, **kwargs):
        def relationship(to, *args, **kwargs):
            tx = Transaction.get_transaction(kwargs.get("tx", None))
            create_relationship_url = self._dic["create_relationship"]
            # Check if target node doesn't exist yet
            if (isinstance(to, TransactionOperationProxy)
                    and not isinstance(to, Node)):
                to_url = "{%s}" % to()["id"]
            else:
                to_url = to.url
            data = {
                "to": to_url,
                "type": relationship_name,
            }
            if "tx" in kwargs and isinstance(kwargs["tx"], Transaction):
                x = kwargs.pop("tx", None)
                del x  # Makes pyflakes happy
            if kwargs:
                data.update({"data": kwargs})
            if tx:
                return tx.append(TX_POST, create_relationship_url,
                                 data=data, obj=self, returns=RELATIONSHIP)
            request = Request(**self._auth)
            response = request.post(create_relationship_url, data=data)
            if response.status_code == 201:
                update_dict = response.json()
                return Relationship(response.headers.get("location",
                                    response.headers.get("content-location")),
                                    auth=self._auth,
                                    update_dict=update_dict)
            elif response.status_code == 404:
                raise NotFoundError(
                    response.status_code,
                    "Node specified by the URI not of \"to\" node not found")
            else:
                msg = "Invalid data sent"
                try:
                    msg += ": " + response.json().get('message')
                except (ValueError, AttributeError, KeyError):
                    pass
                raise StatusException(response.status_code, msg)
        return relationship

    # Special methods for handle pickling manually
    def __getnewargs__(self):
        return tuple()

    def __getstate__(self):
        data = {}
        for key, value in self.__dict__.items():
            try:
                encoded = pickle.dumps(value)
            except pickle.PicklingError:
                encoded = pickle.dumps(pickle.Unpickable())
            data[key] = encoded
        return data

    def __setstate__(self, state):
        for key, value in state.items():
            self.__dict__[key] = pickle.loads(value)

    def _get_relationships(self):
        """
        HACK: Return a 3-methods class: incoming, outgoing and all.
        """
        return Relationships(self, auth=self._auth)
    relationships = property(_get_relationships)

    def _get_id(self):
        return int(self.url.split("/")[-1])
    id = property(_get_id)

    def __hash__(self):
        return hash(self.id)

    def items(self):
        try:
            return self._dic["data"].viewitems()
        except AttributeError:
            return self._dic["data"].items()

    def traverse(self, types=None, order=None, stop=None, returnable=None,
                 uniqueness=None, is_stop_node=None, is_returnable=None,
                 paginated=False, page_size=None, time_out=None,
                 returns=None):
        data = {}
        if order in (BREADTH_FIRST, DEPTH_FIRST):
            data.update({"order": order})
        if isinstance(stop, (int, float)):
            data.update({"max_depth": stop})
        elif stop == STOP_AT_END_OF_GRAPH:
            data.update({'prune_evaluator': {
                'language': 'javascript',
                'body': 'false',
            }})
        if returnable in (RETURN_ALL_NODES, RETURN_ALL_BUT_START_NODE):
            data.update({"return_filter": {
                "language": "builtin",
                "name": returnable,
            }})
        elif returnable:
            data.update({"return_filter": {
                "language": "javascript",
                "body": returnable,
            }})
        if uniqueness in (NODE_GLOBAL, NODE_PATH, NODE_RECENT, NODE,
                          RELATIONSHIP_GLOBAL, RELATIONSHIP_PATH,
                          RELATIONSHIP_RECENT, NONE):
            data.update({"uniqueness": uniqueness})
        if types:
            if not isinstance(types, (list, tuple)):
                types = [types]
            relationships = []
            for relationship in types:
                if relationship.direction == "both":
                    relationships.append({"type": relationship.type})
                else:
                    relationships.append({"type": relationship.type,
                                          "direction": relationship.direction})
            if relationships:
                data.update({"relationships": relationships})
        if returns not in (NODE, RELATIONSHIP, PATH, POSITION):
            returns = NODE
        if ((paginated or page_size or time_out)
                and "paged_traverse" in self._dic):
            traverse_params = []
            if page_size:
                traverse_params.append("pageSize=%s" % page_size)
            if time_out is not None:
                traverse_params.append("leaseTime=%d" % time_out)
            traverse_url = self._dic["paged_traverse"].replace("{returnType}",
                                                               returns)
            traverse_url = traverse_url.replace("{?pageSize,leaseTime}", "")
            if traverse_params:
                traverse_url = "%s?%s" % (traverse_url,
                                          "&".join(traverse_params))
            return PaginatedTraversal(traverse_url, returns, data=data,
                                      auth=self._auth, cypher=self._cypher)
        else:
            traverse_url = self._dic["traverse"].replace("{returnType}",
                                                         returns)
            response = Request(**self._auth).post(traverse_url, data=data)
            if response.status_code == 200:
                results_list = response.json()
                if returns == NODE:
                    return Iterable(Node, results_list, "self",
                                    auth=self._auth, cypher=self._cypher)
                elif returns == RELATIONSHIP:
                    return Iterable(Relationship, results_list, "self",
                                    auth=self._auth)
                elif returns == PATH:
                    return Iterable(Path, results_list, auth=self._auth)
                elif returns == POSITION:
                    return Iterable(Position, results_list, auth=self._auth)
            elif response.status_code == 404:
                raise NotFoundError(
                    response.status_code,
                    "Node or relationship not found"
                )
            else:
                msg = "Invalid data sent"
                try:
                    msg += ": " + response.json().get('message')
                except (ValueError, AttributeError, KeyError):
                    pass
                raise StatusException(response.status_code, msg)

    def _set_labels(self, labels):
        if not isinstance(labels, (tuple, list)):
            labels = [labels]
        self._labels = NodeLabelsProxy(self._dic['labels'], labels=labels,
                                       auth=self._auth, node=Node,
                                       cypher=self._cypher)

    def _get_labels(self):
        if not self._labels:
            self._labels = NodeLabelsProxy(self._dic['labels'],
                                           auth=self._auth, node=Node,
                                           cypher=self._cypher)
        return self._labels

    labels = property(_get_labels, _set_labels)


class PaginatedTraversal(object):
    """
    Class for paged traversals.
    """

    def __init__(self, url, returns, data=None, auth=None, cypher=None):
        self._auth = auth or {}
        self._cypher = cypher
        self.url = url
        self.returns = returns
        self.data = data
        self._results = []
        response = Request(**self._auth).post(self.url, data=self.data)
        if response.status_code == 201:
            self._results = response.json()
            self._next_url = response.headers.get(
                "location",
                response.headers.get("content-location")
            )
        else:
            self._next_url = None

    def __iter__(self):
        return self

    def __next__(self):
        if self._results:
            self._item = False
            if self.returns == NODE:
                results = Iterable(Node, self._results, "self",
                                   auth=self._auth, cypher=self._cypher)
            elif self.returns == RELATIONSHIP:
                results = Iterable(Relationship, self._results, "self",
                                   auth=self._auth)
            elif self.returns == PATH:
                results = Iterable(Path, self._results,
                                   auth=self._auth)
            elif self.returns == POSITION:
                results = Iterable(Position, self._results,
                                   auth=self._auth)
            self._results = []
            if self._next_url:
                response = Request(**self._auth).get(self._next_url)
                if response.status_code == 200:
                    self._results = response.json()
                    content_location = response.headers.get("content-location")
                    self._next_url = response.headers.get("location",
                                                          content_location)
                else:
                    self._next_url = None
            return results
        else:
            raise StopIteration

    def next(self):
        return self.__next__()


class IndexesProxy(dict):
    """
    Class proxy for indexes (nodes and relationships).
    """

    def __init__(self, index_url, index_for=NODE, auth=None, cypher=None):
        self._auth = auth or {}
        self._cypher = cypher
        self.url = index_url
        self._index_for = index_for
        self._dict = self._get_dict()

    def __getitem__(self, attr):
        return self._dict[attr]

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return text_type(self._dict)

    def _get_dict(self):
        indexes_dict = {}
        response = Request(**self._auth).get(self.url)
        if response.status_code == 200:
            indexes_dict = response.json()
            for index_name, index_properties in indexes_dict.items():
                index_props = {}
                for key, val in index_properties.items():
                    index_props[str(key)] = val
                indexes_dict[index_name] = Index(self._index_for, index_name,
                                                 auth=self._auth,
                                                 cypher=self._cypher,
                                                 **index_props)
            return indexes_dict
        elif response.status_code == 404:
            raise NotFoundError(response.status_code, "Indexes not found")
        elif response.status_code == 204:
            return indexes_dict
        else:
            raise StatusException(response.status_code,
                                  "Error requesting indexes with GET %s"
                                  % self.url)

    def create(self, name, **config):
        tx = Transaction.get_transaction(config.pop("tx", None))
        if not config:
            config = {
                'type': INDEX_FULLTEXT,
                'provider': "lucene",
            }
        data = {
            'name': name,
            'config': config,
        }
        if tx:
            url = "/%s/%s" % (INDEX, self._index_for)
            if self._index_for == NODE:
                op = tx.append(TX_POST, url, data=data, obj=self,
                               returns=INDEX_NODE)
            else:
                op = tx.append(TX_POST, url, data=data, obj=self,
                               returns=INDEX_RELATIONSHIP)
            return op
        else:
            if name not in self._dict:
                response = Request(**self._auth).post(self.url, data=data)
                if response.status_code == 201:
                    loaded_dict = response.json()
                    result_dict = {}
                    for key, val in loaded_dict.items():
                        result_dict[str(key)] = val
                    self._dict[name] = Index(self._index_for, name,
                                             auth=self._auth,
                                             cypher=self._cypher,
                                             **result_dict)
                else:
                    msg = "Invalid data sent"
                    try:
                        msg += ": " + response.json().get('message')
                    except (ValueError, AttributeError, KeyError):
                        pass
                    raise StatusException(response.status_code, msg)
            return self._dict[name]

    def get(self, attr, *args, **kwargs):
        if attr in self._dict.keys():
            return self.__getitem__(attr)
        else:
            if args:
                return args[0]
            elif "default" in kwargs:
                return kwargs["default"]
            else:
                if options.SMART_ERRORS:
                    raise KeyError()
                else:
                    raise NotFoundError()

    def items(self):
        return self._dict.items()

    def values(self):
        return self._dict.values()

    def keys(self):
        return self._dict.keys()


class IndexKey(object):
    """
    Intermediate object so that lookups can be done like:
    index[key][value]

    Lookups are formated as http://.../{index_name}/{key}/{value}, so this
    is the object that gets returned by index[key]. The REST request will
    be sent when the value is specified.
    """

    def __init__(self, index_for, url, name, auth=None, cypher=None,
                 key=None, tx=None):
        self._auth = auth or {}
        self._cypher = cypher
        self._key = key
        self._index_for = index_for
        if url[-1] == '/':
            url = url[:-1]
        self.url = url
        self.name = name
        self.tx = tx

    def __getitem__(self, value):
        tx = None
        if isinstance(value, Transaction):
            tx = self.tx or value
            value = value.get_value()
        tx = Transaction.get_transaction(tx)
        url = "%s/%s" % (self.url, smart_quote(value))
        return Index._get_results(url, self._index_for, auth=self._auth,
                                  cypher=self._cypher, tx=tx)

    def __setitem__(self, value, item):
        tx = self.tx
        if isinstance(value, (list, tuple)):
            tx = tx or value[1]
            value = value[0]
        if isinstance(item, Transaction):
            tx = tx or item
            item = item.get_value()
        tx = Transaction.get_transaction(tx)
        # Neo4j hardly crush if you try to index a relationship in a
        # node index and viceversa.
        is_node_index = (self._index_for == NODE
                         and isinstance(item, Node))
        is_relationship_index = (self._index_for == RELATIONSHIP
                                 and isinstance(item, Relationship))
        if not (is_node_index or is_relationship_index
                or TransactionOperationProxy):
            raise TypeError("%s is a %s and the index is for %ss"
                            % (item, self._index_for.capitalize(),
                               self._index_for))
        if isinstance(item, Base):
            url_ref = item.url
        elif isinstance(item, TransactionOperationProxy):
            url_ref = "{%s}" % item()["id"]
        else:
            url_ref = item
        request_url_and_key = self.url.rsplit('/', 1)  # assumes a key
        if PY2:
            # It's URL encoded and we need Unicode
            key = unquote(text_type(request_url_and_key[1]).encode("utf8"))
        else:
            key = unquote(text_type(request_url_and_key[1]))
        data = {"key": key,
                "value": value,  # smart_quote is not needed anymore
                "uri": url_ref}
        if tx:
            request_url = "index/%s/%s" % (self._index_for, self.name)
            op = tx.append(TX_POST, request_url, data=data,
                           obj=self, returns=self._index_for)
            return op
        else:
            request = Request(**self._auth)
            response = request.post(request_url_and_key[0], data=data)
            if response.status_code == 201:
                # Returns object that was indexed
                entity = response.json()
                if self._index_for == NODE:
                    return Node(entity['self'], data=entity['data'],
                                auth=self._auth, update_dict=entity,
                                cypher=self._cypher)
                else:
                    return Relationship(entity['self'],
                                        data=entity['data'],
                                        auth=self._auth)
            else:
                raise StatusException(response.status_code,
                                      "Error requesting index with POST "
                                      "%s, data %s"
                                      % (request_url_and_key[0], url_ref))

    def query(self, value, tx=None):
        url = "%s?query=%s" % (self.url, smart_quote(value))
        return Index._get_results(url, self._index_for, auth=self._auth,
                                  cypher=self._cypher, tx=tx)

    def filter(self, lookups=[], value=None):
        return Index._filter(self, lookups, self._key, value)

    def all(self):
        return self.filter()


class Index(object):
    """
    key/value indexed lookups. Create an index object with GraphDatabase.index.
    The returned object supports dict style lookups, eg index[key][value].
    """

    @staticmethod
    def _get_results(url, node_or_rel, auth={}, cypher=None, tx=None):
        tx = Transaction.get_transaction(tx)
        if tx:
            return tx.append(TX_GET, url, obj=None, returns=ITERABLE,
                             of=node_or_rel)
        else:
            response = Request(**auth).get(url)
            if response.status_code == 200:
                data_list = response.json()
                if node_or_rel == NODE:
                    return Iterable(Node, data_list, "self", auth=auth,
                                    cypher=cypher)
                else:
                    return Iterable(Relationship, data_list, "self", auth=auth)
            elif response.status_code == 404:
                raise NotFoundError(response.status_code,
                                    "Node or relationship not found")
            else:
                raise StatusException(response.status_code,
                                      "Error requesting index with GET %s"
                                      % url)

    def __init__(self, index_for, name, auth=None, cypher=None, **kwargs):
        self._auth = auth or {}
        self._cypher = cypher
        self._index_for = index_for
        self.name = name
        self.template = kwargs.get("template")
        self.provider = kwargs.get("provider")
        self.type = kwargs.get("type")
        url = self.template.replace("{key}/{value}", "")
        if url[-1] == '/':
            url = url[:-1]
        self.url = url

    def __getitem__(self, key):
        if isinstance(key, (list, tuple)):
            tx = key[1]
            key = key[0]
        else:
            tx = None
        tx = Transaction.get_transaction(tx)
        return self.get(key, tx=tx)

    def __eq__(self, obj):
        if not self.url:
            return (obj is None)
        else:
            return (hasattr(obj, "url")
                    and self.url == obj.url
                    and hasattr(obj, "__class__")
                    and self.__class__ == obj.__class__)

    def __ne__(self, obj):
        if not self.url:
            return not (obj is None)
        else:
            return not (hasattr(obj, "url")
                        and self.url == obj.url
                        and hasattr(obj, "__class__")
                        and self.__class__ == obj.__class__)

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"<Neo4j %s: %s>" % (self.__class__.__name__, self.url)

    def add(self, key, value, item, tx=None):
        self.get(key, tx=tx)[value] = item

    def get(self, key, value=None, tx=None):
        if isinstance(key, (list, tuple)):
            tx = tx or key[1]
            key = key[0]
        tx = Transaction.get_transaction(tx)
        index_key = IndexKey(self._index_for,
                             "%s/%s" % (self.url, smart_quote(key)),
                             name=self.name, auth=self._auth,
                             cypher=self._cypher, key=key, tx=tx)
        if value:
            return index_key[smart_quote(value)]
        else:
            return index_key

    def get_or_create(self, key, value, item=None, properties=None,
                      node_from=None, relationship_name=None, node_to=None,
                      tx=None):
        return self._uniqueness("get_or_create", key=key, value=value,
                                item=item, properties=properties,
                                node_from=node_from,
                                relationship_name=relationship_name,
                                node_to=node_to, tx=tx)

    def create_or_fail(self, key, value, item=None, properties=None,
                       node_from=None, relationship_name=None, node_to=None,
                       tx=None):
        return self._uniqueness("create_or_fail", key=key, value=value,
                                item=item, properties=properties,
                                node_from=node_from,
                                relationship_name=relationship_name,
                                node_to=node_to, tx=tx)

    def _uniqueness(self, uniqueness, key, value, item=None, properties=None,
                    node_from=None, relationship_name=None, node_to=None,
                    tx=None):
        url = "%s?uniqueness=%s" % (self.url, uniqueness)
        if item:
            properties = item.properties()
        elif not properties:
            properties = {}
        if self._index_for == NODE:
            data = {
                "key": key,
                "value": value,
                "properties": properties,
            }
        else:
            data = {
                "key": key,
                "value": value,
            }
            if properties:
                data.update({"properties": properties})
            if item:
                data.update({
                    "start": item.start,
                    "end": item.end,
                    "type": item.type,
                })
            else:
                data.update({
                    "start": node_from,
                    "end": node_to,
                    "type": relationship_name,
                })
        tx = Transaction.get_transaction(tx)
        if tx:
            op = tx.append(TX_POST, url, data=data, obj=self,
                           returns=self._index_for)
            return op
        else:
            index_for = self._index_for.capitalize()
            request = Request(**self._auth)
            response = request.post(url, data=data)
            if response.status_code in [200, 201]:
                # Returns object that was indexed
                entity = response.json()
                if self._index_for == NODE:
                    return Node(entity['self'], data=entity['data'],
                                auth=self._auth, update_dict=entity,
                                cypher=self._cypher)
                else:
                    return Relationship(entity['self'],
                                        data=entity['data'],
                                        auth=self._auth)
            elif response.status_code == 409:  # Create or fail, failing
                if options.SMART_ERRORS:
                    raise ValueError("duplicated item in index '%s'"
                                     % index_for)
                else:
                    raise StatusException(response.status_code,
                                          "Duplicated item")
            else:
                if options.SMART_ERRORS:
                    raise KeyError(index_for)
                else:
                    raise StatusException(response.status_code,
                                          "Duplicated item")

    def delete(self, key=None, value=None, item=None, tx=None):
        if not key and not value and not item:
            url = self.template.replace("/{key}/{value}", "")
        else:
            if not isinstance(item, Base):
                raise TypeError("%s has no url attribute" % item)
            if key and value:
                key = smart_quote(key)
                value = smart_quote(value)
                url = self.template.replace("{key}", key).replace("{value}",
                                                                  value)
                url = "%s/%s" % (url, item.id)
                request_url = "index/%s/%s/%s/%s/%s" \
                              % (self._index_for, self.name, key, value,
                                 item.id)
            elif key and not value:
                key = smart_quote(key)
                url = "%s/%s" % (self.template.replace("{key}/{value}", key),
                                 item.id)
                request_url = "index/%s/%s/%s/%s" \
                              % (self._index_for, self.name, key, item.id)
            elif not key and not value:
                url = self.template.replace("{key}/{value}", str(item.id))
                request_url = "index/%s/%s/%s" % (self._index_for, self.name,
                                                  item.id)
            else:
                raise TypeError("delete() takes at least 1 argument, the "
                                "%s to remove" % self._index_for)
        tx = Transaction.get_transaction(tx)
        if tx:
            return tx.append(TX_DELETE, request_url, obj=self)
        else:
            response = Request(**self._auth).delete(url)
            if response.status_code == 404:
                if options.SMART_ERRORS:
                    raise KeyError(self._index_for.capitalize())
                else:
                    index_for = self._index_for.capitalize()
                    raise NotFoundError(response.status_code,
                                        "%s not found" % index_for)
            elif response.status_code != 204:
                raise StatusException(response.status_code)

    def query(self, *args):
        """
        Query a fulltext index by key and query or just a plain Lucene query,

        i1 = gdb.nodes.indexes.get('people',type='fulltext', provider='lucene')
        i1.query('name','do*')
        i1.query('name:do*')

        In this example, the last two line are equivalent.
        """
        if not args or len(args) > 2:
            raise TypeError('query() takes 2 or 3 arguments (a query or a key '
                            'and a query) (%d given)' % (len(args) + 1))
        elif len(args) == 1:
            query, = args
            return self.get('text').query(text_type(query))
        else:
            key, query = args
            index_key = self.get(key)
            if isinstance(query, string_types):
                return index_key.query(query)
            else:
                if query.fielded:
                    raise ValueError('Queries with an included key should '
                                     'not include a field.')
                return index_key.query(text_type(query))

    def filter(self, lookups=[], key=None, value=None):
        return Index._filter(self, lookups, key, value)

    def all(self):
        return self.filter()

    @staticmethod
    def _filter(cls, lookups=[], key=None, value=None):
        if cls._cypher:
            if cls._index_for == NODE:
                start = u"node:"
                returns = Node
            elif cls._index_for == RELATIONSHIP:
                start = u"relationship:"
                returns = Relationship
            else:
                raise CypherException("Index not valid")
            index_name = Base._safe_string(cls.name)
            start = u"%s`%s`" % (start, index_name.replace("`", "\\`"))
            if key:
                key = Base._safe_string(key)
                if value:
                    value = Base._safe_string(value)
                    start = u"%s(\"%s:%s\")" % (start, key, value)
                else:
                    start = u"%s(\"%s:*\")" % (start, key)
            elif value:
                raise CypherException("Index key not valid")
            else:
                start = u"%s(\"*:*\")" % start
            if not isinstance(lookups, (list, tuple)):
                lookups = [lookups]
            types = {
                "node": Node,
                "relationship": Relationship,
                "path": Path,
                "position": Position,
            }
            return FilterSequence(cls._cypher, cls._auth, start=start,
                                  types=types, lookups=lookups,
                                  returns=returns)
        else:
            raise CypherException


class RelationshipsProxy(dict):
    """
    Class proxy for relationships in order to allow get a relationship by id
    and create new relationships through calling.
    """

    def __init__(self, relationship, relationship_index, auth=None,
                 cypher=None):
        self._auth = auth or {}
        self._cypher = cypher
        self._relationship = relationship
        self._relationship_index = relationship_index

    def __getitem__(self, key, tx=None):
        tx = Transaction.get_transaction(tx)
        if tx:
            return tx.append(TX_GET, "%s/%s" % (self._relationship, key),
                             obj=self)
        else:
            return Relationship("%s/%s" % (self._relationship, key),
                                auth=self._auth)

    def get(self, key, *args, **kwargs):
        tx = Transaction.get_transaction(kwargs.get("tx", None))
        try:
            return self.__getitem__(key, tx=tx)
        except (KeyError, NotFoundError, StatusException):
            if args:
                return args[0]
            elif "default" in kwargs:
                return kwargs["default"]
            else:
                raise NotFoundError()

    def create(self, node_from, relationship_name, node_to, **kwargs):
        return getattr(node_from, relationship_name)(node_to, **kwargs)

    def delete(self, key, tx=None):
        tx = Transaction.get_transaction(tx)
        if tx:
            return self.__getitem__(key, tx=tx)
        else:
            relationship = self.__getitem__(key)
            del relationship

    def filter(self, lookups=[], start=None):
        return elements_filter(self, lookups=lookups, start=start,
                               returns=Relationship)

    def all(self):
        return self.filter()

    def _indexes(self):
        if self._relationship_index:
            return IndexesProxy(self._relationship_index, RELATIONSHIP,
                                auth=self._auth, cypher=self._cypher)
    indexes = property(_indexes)


class Relationships(object):
    """
    Relationships class for a node.
    """

    def __init__(self, node, auth=None):
        self._auth = auth or {}
        self._node = node
        self._pattern = "{-list|&|types}"
        self._dict = {}
        self._len = 0

    def __getattr__(self, relationship_type):
        # auth = object.__getattribute__(self, "_auth")

        def get_relationships(types=None, *args, **kwargs):
            tx = Transaction.get_transaction(kwargs.get("tx", None))
            if relationship_type in ["all", "incoming", "outgoing"]:
                if types and isinstance(types, (tuple, list)):
                    key = "%s_typed_relationships" % relationship_type
                    url_string = self._node._dic[key]
                    url = url_string.replace(self._pattern, "&".join(types))
                else:
                    key = "%s_relationships" % relationship_type
                    url = self._node._dic[key]
                if tx:
                    return tx.append(TX_GET, url, obj=self)
                response = Request(**self._auth).get(url)
                if response.status_code == 200:
                    relationship_list = response.json()
                    relationships = Iterable(Relationship, relationship_list,
                                             "self", auth=self._auth)
                    # relationships = [Relationship(r["self"])
                    #                  for r in relationship_list]
                    self._dict[relationship_type] = relationships
                    return self._dict[relationship_type]
                elif response.status_code == 404:
                    if options.SMART_ERRORS:
                        return []
                    else:
                        raise NotFoundError(response.status_code,
                                            "Node or relationship not found")
                else:
                    if options.SMART_ERRORS:
                        raise KeyError("Node not found")
                    else:
                        raise StatusException(response.status_code,
                                              "Node not found")
            raise NameError("name %s is not defined" % relationship_type)

        return get_relationships

    def __len__(self, tx=None):
        tx = Transaction.get_transaction(tx)
        if tx:
            # We have to avoid a infinite recursion loop
            # return len(self.__getattr__("all")(tx=tx))
            pass
        elif "all" in self._dict:
            self._len = len(self._dict["all"])
        else:
            self._len = len(self.__getattr__("all")())
        return self._len

    def count(self, tx=None):
        return self.__len__(tx=tx)

    def __getitem__(self, index, tx=None):
        tx = Transaction.get_transaction(tx)
        return self.__getattr__("all")(tx=tx)[index]

    def create(self, relationship_name, to, **kwargs):
        # TODO: Improve the unicode checking
        try:
            return self._node._create_relationship(relationship_name)(to,
                                                                      **kwargs)
        except (KeyError, UnicodeEncodeError, UnicodeError):
            safe_name = smart_quote(relationship_name)
            return getattr(self._node, safe_name)(to, **kwargs)

    def get(self, index, tx=None):
        tx = Transaction.get_transaction(tx)
        return self.__getattr__(index, tx=tx)


class Relationship(Base):
    """
    Relationship class.
    """

    def _get_start(self):
        return Node(self._dic['start'], auth=self._auth, cypher=self._cypher)
    start = property(_get_start)

    def _get_end(self):
        return Node(self._dic['end'], auth=self._auth, cypher=self._cypher)
    end = property(_get_end)

    def _get_type(self):
        if PY2:
            return self._dic['type'].encode("utf8")
        else:
            return self._dic['type']
    type = property(_get_type)

    def _get_id(self):
        return int(self.url.split("/")[-1])
    id = property(_get_id)


class Path(object):
    """
    Path class for return type PATH in traversals.
    """

    def __init__(self, dic, auth=None, cypher=None):
        self._auth = auth or {}
        self._cypher = cypher
        self._dic = dic
        self._length = int(dic["length"])
        self._nodes = []
        self._relationships = []
        self._iterable = []
        self._start = Node(self._dic["start"], auth=self._auth,
                           cypher=self._cypher)
        self._end = Node(self._dic["end"], auth=self._auth,
                         cypher=self._cypher)
        for i in range(0, len(dic["relationships"])):
            node = Node(dic["nodes"][i], auth=self._auth, cypher=self._cypher)
            self._nodes.append(node)
            relationship = Relationship(dic["relationships"][i],
                                        auth=self._auth)
            self._relationships.append(relationship)
            self._iterable.append(node)
            self._iterable.append(relationship)
        node = Node(dic["nodes"][-1], auth=self._auth, cypher=self._cypher)
        self._nodes.append(node)
        self._iterable.append(node)

    def __len__(self):
        return self._length

    def __iter__(self):
        return iter(self._iterable)

    def _get_start(self):
        return self._start
    start = property(_get_start)

    def _get_end(self):
        return self._end
    end = property(_get_end)

    def _get_weight(self):
        return self._dic.get("weight", None)
    weight = property(_get_weight)

    def _get_nodes(self):
        return self._nodes
    nodes = property(_get_nodes)

    def _get_relationships(self):
        return self._relationships
    relationships = property(_get_relationships)

    def _get_last_relationship(self):
        return self._relationships[-1]
    last_relationship = property(_get_last_relationship)


class Position(object):
    """
    Position class for return type POSITION in traversals.
    """

    def __init__(self, dic, auth=None, cypher=None, **kwargs):
        self._auth = auth or {}
        self._cypher = cypher
        self._node = Node(dic["node"], auth=self._auth, cypher=self._cypher)
        self._depth = int(dic["depth"])
        relationship = Relationship(dic.get("last relationship",
                                    dic.get("last_relationship", None)),
                                    auth=self._auth)
        self._last_relationship = relationship
        self._path = Path(dic["path"], auth=self._auth, cypher=self._cypher)

    def _get_node(self):
        return self._node
    node = property(_get_node)

    def _get_depth(self):
        return self._depth
    depth = property(_get_depth)

    def _get_last_relationship(self):
        return self._last_relationship
    last_relationship = property(_get_last_relationship)

    def _get_path(self):
        return self._path
    path = property(_get_path)


class BaseInAndOut(object):
    """
    Base class for Incoming, Outgoing and Undirected relationships types.
    """

    def __init__(self, direction):
        self.direction = direction

    def get(self, attr):
        return self.__getattr__(attr)

    def __getattr__(self, attr):
        if self.direction == "both":
            warnings.warn("Deprecated, use \"All\" ('both') instead.",
                          DeprecationWarning)
        # Using an anonymous class
        direction = self.direction
        return type("", (object, ), {
            'direction': property(lambda self: direction),
            'type': property(lambda self: attr),
        })()

All = BaseInAndOut(direction=RELATIONSHIPS_ALL)
Incoming = BaseInAndOut(direction=RELATIONSHIPS_IN)
Outgoing = BaseInAndOut(direction=RELATIONSHIPS_OUT)
Undirected = BaseInAndOut(direction="both")  # Deprecated, use "All" instead


class Direction(object):
    ANY = All
    INCOMING = Incoming
    OUTGOING = Outgoing


class ExtensionModule(dict):
    def __init__(self, klass_name, auth):
        self.klass_name = klass_name
        self.auth = auth
        self.cache = {}

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"<Neo4j %s: %s>" % (self.__class__.__name__,
                                    text_type(self.klass_name.keys()))

    def __getitem__(self, attr):
        return self.__getattr__(attr)

    def get(self, attr):
        return self.__getattr__(attr)

    def __getattr__(self, attr):
        if attr in self.cache:
            return self.cache[attr]
        else:
            self.cache[attr] = Extension(self.klass_name[attr], auth=self.auth)
            return self.cache[attr]


class ExtensionsProxy(dict):
    """
    Class proxy for extensions in order to allow get an extension by module
    and class name and executing with the right params through calling.
    """

    def __init__(self, extensions, auth=None, cypher=None):
        self._extensions = extensions
        self._dict = {}
        self._auth = auth or {}
        self._cypher = cypher

    def __getitem__(self, attr):
        return self.__getattr__(attr)

    def __getattr__(self, attr):
        if attr in self._dict:
            return self._dict[attr]
        self._dict[attr] = ExtensionModule(self._extensions[attr], self._auth)
        return self._dict[attr]

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        if not self._dict:
            self._dict = self._get_dict()
        return text_type(self._dict)

    def _get_dict(self):
        return dict([(key, self.__getattr__(key))
                     for key in self._extensions.keys()])

    def get(self, attr, *args, **kwargs):
        if attr in self._dict.keys():
            return self.__getattr__(attr)
        else:
            if args:
                return args[0]
            elif "default" in kwargs:
                return kwargs["default"]
            else:
                raise NotFoundError()

    def items(self):
        if not self._dict:
            self._dict = self._get_dict()
        return self._dict.items()

    def values(self):
        if not self._dict:
            self._dict = self._get_dict()
        return self._dict.values()

    def keys(self):
        if not self._dict:
            self._dict = self._get_dict()
        return self._dict.keys()

    # Special methods for handle pickling manually
    def __getnewargs__(self):
        return tuple()

    def __getstate__(self):
        data = {}
        for key, value in self.__dict__.items():
            try:
                encoded = pickle.dumps(value)
            except pickle.PicklingError:
                encoded = pickle.dumps(pickle.Unpickable())
            data[key] = encoded
        return data

    def __setstate__(self, state):
        for key, value in state.items():
            self.__dict__[key] = pickle.loads(value)


class Extension(object):
    """
    Extension class.
    """

    def __init__(self, url, auth=None, cypher=None):
        self._auth = auth or {}
        self._cypher = cypher
        self._dic = {}
        if url.endswith("/"):
            url = url[:-1]
        self.url = url
        response = Request(**self._auth).get(self.url)
        if response.status_code == 200:
            self._dic.update(response.json().copy())
            self.description = self._dic['description']
            self.name = self._dic['name']
            self.extends = self._dic['extends']
            self.parameters = self._dic['parameters']
        else:
            raise NotFoundError(response.status_code, "Unable get extension")

    def __call__(self, *args, **kwargs):
        # The returns param is a temporary solution while
        # a proper way to get the data type of returned values by
        # the extensions is implemented in Neo4j
        returns = kwargs.pop("returns", None)
        parameters = self._parse_parameters(args, kwargs)
        response = Request(**self._auth).post(self.url, data=parameters)
        if response.status_code == 200:
            result = response.json()
            # Another option is to inspect the results
            if not returns:
                if isinstance(result, (tuple, list)) and len(result) > 0:
                    returns = result[0].get("self", None)
                elif isinstance(result, dict) and "self" in result:
                    returns = result.get("self", None)
            if returns and RAW in returns:
                return result
            if isinstance(result, (tuple, list)) and returns:
                if NODE in returns:
                    return Iterable(Node, result, "self", auth=self._auth,
                                    cypher=self._cypher)
                elif RELATIONSHIP in returns:
                    return Iterable(Relationship, result, "self",
                                    auth=self._auth)
                elif PATH in returns or FULLPATH in returns:
                    return Iterable(Path, result, auth=self._auth)
                elif POSITION in returns:
                    return Iterable(Position, result, auth=self._auth)
            elif isinstance(result, dict) and returns:
                if NODE in returns:
                    return Node(result["self"], data=result, auth=self._auth,
                                cypher=self._cypher)
                elif RELATIONSHIP in returns:
                    return Relationship(result["self"], data=result,
                                        auth=self._auth, cypher=self._cypher)
                elif PATH in returns:
                    return Path(result, auth=self._auth, cypher=self._cypher)
                elif POSITION in returns:
                    return Position(result, auth=self._auth,
                                    cypher=self._cypher)
            elif result:
                return result
            else:
                return []
        elif response.status_code == 404:
            raise NotFoundError(response.status_code, "Extension not found")
        else:
            msg = "Invalid data sent"
            try:
                msg += ": " + response.json()['message']
            except (ValueError, AttributeError, KeyError, TypeError):
                pass
            raise StatusException(response.status_code, msg)

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"<Neo4j %s: %s>" % (self.__class__.__name__, self.url)

    def _parse_parameters(self, args, kwargs):
        if not args and not kwargs:
            return kwargs
        params_len = len(self.parameters)
        args_len = len(args)
        kwargs_len = len(kwargs)
        if args_len + kwargs_len > params_len:
            raise TypeError("%s() take at most %s arguments (%s given)"
                            % (self.name, params_len, args_len + kwargs_len))
        required = [np for np in self.parameters if np["optional"] is False]
        required_len = len(required)
        if args_len + kwargs_len < required_len:
            raise TypeError("%s() take at least %s arguments (%s given)"
                            % (self.name, required_len, args_len + kwargs_len))
        params_kwargs = {}
        if args:
            for i, arg in enumerate(args):
                key = required[i]["name"]
                params_kwargs[key] = args[i]
        if kwargs:
            for param, value in kwargs.items():
                has_param = (len([np for np in self.parameters
                                  if np["name"] == param]) != 0)
                if param not in params_kwargs and has_param:
                    params_kwargs[param] = value
        return self._parse_types(params_kwargs)

    def _parse_types(self, kwargs):
        params_kwargs = {}
        for param, value in kwargs.items():
            if isinstance(value, Base):
                params_kwargs[param] = value.url
            else:
                params_kwargs[param] = value
        return params_kwargs


def elements_filter(cls, lookups=[], start=None, returns=None):
    if isinstance(start, (Index, IndexKey)):
        return start.filter(lookups=lookups)
    elif cls._cypher:
        if start:
            starts = []
            if not isinstance(start, (list, tuple)):
                start = [start]
            for start_element in start:
                try:
                    starts.append(text_type(start_element.id))
                except AttributeError:
                    starts.append(text_type(start_element))
        else:
            starts = u"*"
        if returns is Node:
            start = u"node(%s)" % u", ".join(starts)
        elif returns is Relationship:
            start = u"rel(%s)" % u", ".join(starts)
        else:
            raise CypherException
        if not isinstance(lookups, (list, tuple)):
            lookups = [lookups]
        types = {
            "node": Node,
            "relationship": Relationship,
            "path": Path,
            "position": Position,
        }
        return FilterSequence(cls._cypher, cls._auth, start=start,
                              types=types, lookups=lookups, returns=returns)
    else:
        raise CypherException
