# -*- coding: utf-8 -*-
try:
    import cPickle as pickle
except:
    import pickle
import json
import urllib
import urlparse
import weakref
import warnings
from lucenequerybuilder import Q

import options
from constants import (BREADTH_FIRST, DEPTH_FIRST,
                       STOP_AT_END_OF_GRAPH,
                       NODE_GLOBAL, NODE_PATH, NODE_RECENT,
                       RELATIONSHIP_GLOBAL, RELATIONSHIP_PATH,
                       RELATIONSHIP_RECENT, NONE,
                       NODE, RELATIONSHIP, PATH, POSITION,
                       INDEX_FULLTEXT, TX_GET, TX_PUT, TX_POST, TX_DELETE,
                       RELATIONSHIPS_ALL, RELATIONSHIPS_IN, RELATIONSHIPS_OUT,
                       RETURN_ALL_NODES, RETURN_ALL_BUT_START_NODE)
from request import (Request, NotFoundError, StatusException,
                     TransactionException)

__all__ = ["GraphDatabase", "Incoming", "Outgoing", "Undirected",
           "StopAtDepth", "NotFoundError", "StatusException", "Q"]


DEFAULT_NEO_NODE_DIC = {
    "outgoing_relationships" : "{URL}/relationships/out",
    "traverse" : "{URL}/traverse/{returnType}",
    "all_typed_relationships" : "{URL}/relationships/all/{-list|&|types}",
    "property" : "{URL}/properties/{key}",
    "self" : "{URL}",
    "properties" : "{URL}/properties",
    "outgoing_typed_relationships" : "{URL}/relationships/out/{-list|&|types}",
    "incoming_relationships" : "{URL}/relationships/in",
    "extensions" : {},
    "create_relationship" : "{URL}/relationships",
    "paged_traverse" : "{URL}/paged/traverse/{returnType}{?pageSize,leaseTime}",
    "all_relationships" : "{URL}/relationships/all",
    "incoming_typed_relationships" : "{URL}/relationships/in/{-list|&|types}"
}

DEFAULT_NEO_RELATIONSHIP_DIC = {
    "start" : "{START_URL}",
    "self" : "{URL}",
    "property" : "{URL}/properties/{key}",
    "properties" : "{URL}/properties",
    "extensions" : {},
    "end" : "{END_URL}"
}

class StopAtDepth(object):
    """
    Only traverse to a certain depth.
    """

    def __init__(self, depth):
        self.depth = depth

    def __get__(self):
        return self.depth


class MetaTraversal(type):
    """
    Metaclass for adding default attributes to Traversal class.
    """

    def __new__(cls, name, bases, dic):
        for attr in ["types", "order", "stop", "returnable", "uniqueness",
                     "paginated", "page_size", "time_out", "returns"]:
            dic[attr] = dic.get(attr, None)
        dic["is_returnable"] = dic.get("is_returnable",
                                       dic.get("isReturnable", None))
        dic["is_stop_node"] = dic.get("is_stop_node",
                                      dic.get("isStopNode", None))
        return type.__new__(cls, name, bases, dic)


class GraphDatabase(object):
    """
    Main class for connection to Ne4j standalone REST server.
    """
    
    def __init__(self, url):
        self._transactions = {}
        self.url = None
        if url.endswith("/"):
            self.url = url
        else:
            self.url = "%s/" % url
        response, content = None, None
        try:
            response, content = Request().get(url)
        except Exception:
            raise NotFoundError(result="Unable get root")
        if response.status == 200:
            response_json = json.loads(content)
            self._relationship_index = response_json['relationship_index']
            self._node = response_json['node']
            self._node_index = response_json['node_index']
            self._reference_node = response_json['reference_node']
            self._extensions_info = response_json['extensions_info']
            self._extensions = response_json['extensions']
            self.extensions = ExtensionsProxy(self._extensions)
            self.nodes = NodesProxy(self._node, self._reference_node,
                                    self._node_index)
            # Backward compatibility. The current style is more pythonic
            self.node = self.nodes
            # HACK: Neo4j doesn't provide the URLs to access to relationships
            url_parts = self._node.rpartition("node")
            self._relationship = "%s%s%s" % (url_parts[0], RELATIONSHIP,
                                             url_parts[2])
            self.relationships = RelationshipsProxy(self._relationship,
                                                    self._relationship_index)
            self.Traversal = self._get_traversal_class()
            self._batch = "%sbatch" % self.url
        else:
            raise NotFoundError(response.status, "Unable get root")

    def _get_reference_node(self):
        return Node(self._reference_node)
    reference_node = property(_get_reference_node)

    def traverse(self, *args, **kwargs):
        return self.reference_node.traverse(*args, **kwargs)

    def _get_traversal_class(self):
        cls = self

        class Traversal(object):
            __metaclass__ = MetaTraversal

            def __init__(self, start_node=None):
                if start_node and isinstance(start_node, Node):
                    self.start_node = start_node
                else:
                    self.start_node = cls.reference_node
                is_returnable = self.is_returnable
                is_stop_node = self.is_stop_node
                results = self.start_node.traverse(types=self.types,
                                                   order=self.order,
                                                   stop=self.stop,
                                                   returnable=self.returnable,
                                                   uniqueness=self.uniqueness,
                                                   is_stop_node=is_stop_node,
                                                   is_returnable=is_returnable,
                                                   paginated=self.paginated,
                                                   page_size=self.page_size,
                                                   time_out=self.time_out,
                                                   returns=self.returns)
                self._items = results
                self._index = len(results)

            def __iter__(self):
                return self

            def next(self):
                if self._index == 0:
                    raise StopIteration
                self._index = self._index - 1
                return self._items[self._index]

        return Traversal

    def transaction(self, using_globals=True, commit=True, update=True,
                    transaction_id=None, context=None):
        if transaction_id not in self._transactions:
            transaction_id = len(self._transactions.keys())
        self._transactions[transaction_id] = Transaction(self, transaction_id,
                                                         context or {},
                                                         commit=commit,
                                                         update=update)
        if using_globals:
            globals()[options.TX_NAME] = self._transactions[transaction_id]
        return self._transactions[transaction_id]


class TransactionOperationProxy(dict, object):
    """
    TransactionOperationProxy class. A proxy to convert transaction operations
    into final instances of Node or Relationship.
    """

    def __init__(self, return_type=None, obj=None, callback=None, attr=None,
                 **kwargs):
        #TODO it would be good is proxies knew the class they'll be changed to
        #for further emulating of the Node/Relationship/Path/Position interface
        # - @mhluongo
        self._self = None
        self._return_type = return_type
        if obj:
            self._object_ref = weakref.ref(obj)
        else:
            self._object_ref = None
        self._attribute = attr
        self._callback = callback
        super(TransactionOperationProxy, self).__init__(kwargs)

    def __getattribute__(self, attr):
        try:
            if attr not in ("_self", "_callback"):
                return getattr(object.__getattribute__(self, "_self"), attr)
        except AttributeError:
            pass
        return object.__getattribute__(self, attr)

    def __setattribute__(self, attr, val):
        if attr in ("_object_ref", "_attribute", "_callback"):
            object.__setattribute__(self, attr, val)
        elif attr != "_self":
            setattr(self._self, attr, val)
        else:
            dict.__setattribute__(self, attr, val)

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        attr = "__unicode__"
        try:
            return getattr(object.__getattribute__(self, "_self"), attr)()
        except AttributeError:
            pass
        return object.__repr__(self)

    def __getitem__(self, key):
        attr = "__getitem__"
        try:
            return getattr(object.__getattribute__(self, "_self"), attr)(key)
        except AttributeError:
            pass
        return dict.__getitem__(self, key)

    def get_object(self):
        if self._object_ref:
            return self._object_ref()
        else:
            return None

    def get_attribute(self):
        return self._attribute

    def change(self, cls, url, data=None):
        method = cls.from_url if hasattr(cls, 'from_url') else cls
        self.change_to_object(method(url, update_dict=data))

    def change_to_object(self, obj):
        self._self = obj
        if self._callback:
            self._callback(self._self)
            del self._callback

    #####################################
    # MOCK NODE/RELATIONSHIP ATTRIBUTES #
    #####################################
    
    #these are hacks

    @property
    def url(self):
        return '{%d}' % self['id']

    @property
    def relationships(self):
        return Node(self.url, update=False).relationships

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

        >>> with gdb.transaction(using_globals=False) as tx:
           ...:     n[key] = tx(value)
        """
        self._value = value
        return self

    def get_value(self):
        return self._value

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        del self._class._transactions[self.id]
        if options.TX_NAME in globals():
            del globals()[options.TX_NAME]
        if self.auto_commit:
            return self.commit(type, value, traceback)
        #TODO It would be good if this only returned True for tx-related errors 
        #and not, say, AssertionError, to allow predictable python debugging
        return True

    def _results_list_to_dict(self, results):
        def returns(dic):
            if RELATIONSHIP in dic['self']:
                return Relationship
            elif NODE in dic['self']:
                return Node
            else:
                return None

        result_dict = {}
        for result in results:
            result_id = result.pop("id")
            if "body" in result:
                if not isinstance(result['body'], dict)\
                   and len(result['body']) > 0:
                    result_dict[result_id] = []
                    for result_el in result['body']:
                        result_el['returns'] = returns(result_el)
                        result_dict[result_id].append(result_el)
                elif "self" in result["body"]:
                    result["returns"] = returns(result['body'])
                else:
                    if 'provider' in result['body']:
                        result['returns'] = Index
            if "returns" in result:
                result_dict[result_id] = result
        return result_dict

    def _batch(self):
        response, content = Request().post(self.url, data=self.operations)
        if response.status == 200:
            results_list = json.loads(content)
            results_dict = self._results_list_to_dict(results_list)
            return results_dict
        else:
            raise TransactionException(response.status)

    def cancel(self):
        del self._class._transactions[self.id]
        if options.TX_NAME in globals():
            del globals()[options.TX_NAME]
        del self

    def commit(self, *args, **kwargs):
        results = self._batch()
        # Objects to update
        if self.auto_update:
            for operation in self.operations:
                on_object = operation.get_object()
                if hasattr(on_object, "update"):
                    on_object.update(extensions=False, delete_on_not_found=True)
        # Objects to return
        for referenced_object in self.references:
                ref_object = referenced_object()
                result = results[ref_object["id"]]
                if not isinstance(result, dict):
                    iter_for = result[0]['returns']
                    ref_object.change_to_object(Iterable(iter_for, result))
                elif "returns" in result:
                    if "location" in result:
                        cls = result["returns"]
                        url = result["location"]
                    elif "body" in result:
                        cls = result["returns"]
                        url = result["body"]["self"]
                    if cls and url:
                        ref_object.change(cls, url, data=result)
        self.references = []
        self.operations = []
        # Destroy the object after commit
        self = None
        if "type" in kwargs and isinstance(kwargs["type"], Exception):
            raise kwargs["type"]
        else:
            return True

    def subscribe(self, method, url, data=None, obj=None, callback=None):
        to_url = url.replace(self._class.url, "")
        if not to_url.startswith('{'):
            to_url += '/'
        params = {
            "method": method,
            "to": to_url,
            "id": len(self.operations),
        }
        if data:
            params.update({"body": data})
        # Reunify PUT methods in just one
        transaction_operation = None
        for i, operation in enumerate(self.operations):
            if (operation["method"] == params["method"] == TX_PUT
                and operation["to"] == params["to"]):
                if "body" in operation:
                    self.operations[i]["body"].update(params["body"])
                else:
                    self.operations[i]["body"] = params["body"]
                transaction_operation = operation
                break
        if not transaction_operation:
            transaction_operation = TransactionOperationProxy(obj=obj,
                                                              callback=callback,
                                                              **params)
            self.operations.append(transaction_operation)
            if method in (TX_POST, TX_GET):
                self.references.append(weakref.ref(transaction_operation))
        return transaction_operation

    @staticmethod
    def get_transaction(tx=None):
        if not tx and options.TX_NAME in globals():
            return globals()[options.TX_NAME]
        elif isinstance(tx, Transaction):
            return tx
        elif (isinstance(tx, (list, tuple)) and len(tx) > 1
              and isinstance(tx[-1], Transaction)):
            return tx[-1]
        else:
            return None

class RequestBuilder(dict):
    """
    Base class to build request URLs for operations on Neo4j objects over REST.

    This class was created to separate operation URL creation from the state
    maintenance required of classes like Node and Relationship.
    """
    fallback_dic = {}

    def __init__(self, url, dic={}):
        super(RequestBuilder, self).__init__(**dic)
        if url is not None and url.endswith("/"):
            url = url[:-1]
        self.url = url
        self.update(dic)

    def __getitem__(self, item):
        if item == 'data' and item not in self:
            self[item] = {}
            return self[item]
        else:
            try:
                return super(RequestBuilder, self).__getitem__(item)
            except KeyError:
                if item in self.fallback_dic:
                    return self._fallback_template(self.fallback_dic[item])
                else:
                    raise

    def property_url(self, key):
        return self['property'].replace("{key}", smart_quote(key))

    def properties_url(self):
        return self['properties']

    def transaction_url(self):
        return self.property_url('')

    def _fallback_template(self, template_url):
        return template_url.replace('{URL}',self.url)

    def copy(self):
        return type(self)(self.url, dic=self)

class NodeRequestBuilder(RequestBuilder):
    fallback_dic = DEFAULT_NEO_NODE_DIC

    def create_relationship_url(self):
        return self['create_relationship']

    def traverse_url(self, return_type):
        return self["traverse"].replace("{returnType}", return_type)

    def paged_traverse_url(self, return_type, page_size=None, time_out=None):
        url = self["paged_traverse"].replace("{returnType}", return_type)
        url = url.replace("{?pageSize,leaseTime}", "")
        parts = urlparse.urlsplit(url)
        query = urlparse.parse_qsl(parts[3])
        if page_size is not None:
            query.append(('pageSize', str(page_size)))
        if time_out is not None:
            query.append(('leaseTime', str(time_out)))
        return urlparse.urlunsplit(parts[:3] + (urllib.urlencode(query),) 
                                   + parts[-1:])

class RelationshipRequestBuilder(RequestBuilder):
    fallback_dic = DEFAULT_NEO_RELATIONSHIP_DIC

    def __init__(self, url, start_url, end_url, **kwargs):
        super(RelationshipRequestBuilder, self).__init__(url, **kwargs)
        self.start_url = start_url
        self.end_url = end_url

    def _fallback_template(self, template_url):
        temp = super(RelationshipRequestBuilder, self).\
                _fallback_template(template_url)
        return temp.replace('{START_URL}', self.start_url)\
                .replace('{END_URL}', self.end_url)

class Base(object):
    """
    Base class.
    """

    def __init__(self, url, create=False, update=True, update_dict={}, data={},
                 request_builder=None):
        if request_builder is not None:
            self._dic = request_builder
        else:
            self._dic = RequestBuilder(url)
        self._dic.update(update_dict)
        self._update_dict_data()
        if create:
            response, content = Request().post(url, data=data)
            if response.status == 201:
                self._dic.update(data.copy())
                self._update_dict_data()
                self._dic.url = response.get("location")
            else:
                raise NotFoundError(response.status, "Invalid data sent")
        if update:
            self.update()

    @property
    def url(self):
        return self._dic.url

    def _update_dict_data(self):
        self._dic['data'] = dict((self._safe_string(k), self._safe_string(v))
                          for k, v in self._dic['data'].items())

    def _safe_string(self, s):
        return unicode(s.decode("utf-8"))

    def update(self, extensions=True, delete_on_not_found=False):
        response, content = Request().get(self.url)
        if response.status == 200:
            data = json.loads(content).copy()
            self._dic.update(data)
            if extensions:
                self._extensions = data.get('extensions', {})
                if self._extensions:
                    self.extensions = ExtensionsProxy(self._extensions)
        elif delete_on_not_found and response.status == 404:
            self._dic.url = None
            self._dic = type(self._dic)(None)
            self = None
            del self
        else:
            raise NotFoundError(response.status, "Unable get object")

    def delete(self, key=None, tx=None):
        if key:
            return self.__delitem__(key, tx=tx)
        tx = Transaction.get_transaction(tx)
        if tx:
            return tx.subscribe(TX_DELETE, self.url, obj=self)
        response, content = Request().delete(self.url)
        if response.status == 204:
            del self
        elif response.status == 404:
            raise NotFoundError(response.status, "Node or property not found")
        else:
            raise StatusException(response.status, "Node could not be "\
                                                   "deleted (still has " \
                                                   "relationships?)")

    def __getitem__(self, key, tx=None):
        property_url = self._dic.property_url(key)
        tx = Transaction.get_transaction(tx)
        if tx:
            return tx.subscribe(TX_GET, property_url, obj=self)
        response, content = Request().get(property_url)
        if response.status == 200:
            self._dic['data'][key] = json.loads(content)
        else:
            if options.SMART_ERRORS:
                raise KeyError()
            else:
                raise NotFoundError(response.status,
                                    "Node or propery not found")
        return self._dic['data'][key]

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
        return obj in self._dic['data']

    def __setitem__(self, key, value, tx=None):
        if isinstance(key, (list, tuple)):
            tx = tx or key[1]
            key = key[0]
        if isinstance(value, Transaction):
            tx = tx or value
            value = value.get_value()
        property_url = self._dic.property_url(key)
        tx = Transaction.get_transaction(tx)
        if tx:
            transaction_url = self._dic.transaction_url()
            return tx.subscribe(TX_PUT, transaction_url, {key: value}, obj=self)
        response, content = Request().put(property_url, data=value)
        if response.status == 204:
            self._dic['data'].update({key: value})
        elif response.status == 404:
            raise NotFoundError(response.status, "Node or property not found")
        else:
            raise StatusException(response.status, "Invalid data sent")

    def set(self, key, value, tx=None):
        tx = Transaction.get_transaction(tx)
        if tx:
            return self.__setitem__(key, value, tx=tx)
        self.__setitem__(key, value)

    def __delitem__(self, key, tx=None):
        property_url = self._dic.property_url(key)
        tx = Transaction.get_transaction(tx)
        if tx:
            return tx.subscribe(TX_DELETE, property_url, obj=self)
        response, content = Request().delete(property_url)
        if response.status == 204:
            del self._dic['data'][key]
        elif response.status == 404:
            if options.SMART_ERRORS:
                raise KeyError()
            else:
                raise NotFoundError(response.status,
                                    "Node or propery not found")
        else:
            raise StatusException(response.status, "Node or propery not found")

    def __len__(self):
        return len(self._dic['data'])

    def __iter__(self):
        return self._dic['data'].__iter__()

    def __eq__(self, obj):
        if not self.url and not self._dic['data']:
            return (obj == None)
        else:
            return (hasattr(obj, "url")
                    and self.url == obj.url
                    and hasattr(obj, "__class__")
                    and self.__class__ == obj.__class__)

    def __ne__(self, obj):
        return not self.__cmp__(obj)

    def __nonzero__(self):
        return bool(self.url) or bool(self._dic['data'])

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
        return self._dic.get('data',{})

    def _set_properties(self, props={}):
        if not props:
            return None
        properties_url = self._dic.properties_url()
        response, content = Request().put(properties_url, data=props)
        if response.status == 204:
            self._dic['data'] = props.copy()
            self._update_dict_data()
            return props
        elif response.status == 400:
            raise StatusException(response.status, "Invalid data sent")
        else:
            raise NotFoundError(response.status, "Properties not found")

    def _del_properties(self):
        properties_url = self._dic.properties_url()
        response, content = Request().delete(properties_url)
        if response.status == 204:
            self._dic['data'] = {}
        else:
            raise NotFoundError(response.status, "Properties not found")
    # TODO: Create an own Property class to handle transactions
    properties = property(_get_properties, _set_properties, _del_properties)


class Iterable(list):
    """
    Class to iterate among returned objects.
    """

    def __init__(self, cls, lst, attr=None):
        self._list = lst
        self._index = len(lst)
        self._class = cls
        self._attribute = attr
        super(Iterable, self).__init__(lst)

    def _get_object(self, element):
        if self._attribute:
            element = element[self._attribute]
        if isinstance(element, dict):
            return self._class(element['self'], update_dict=element, update=False)
        else:
            return self._class(element)

    def __getitem__(self, index):
        if isinstance(index, slice):
            indices = index.indices(len(self))
            return [self[i] for i in range(*indices)]
        else:
            elto = super(Iterable, self).__getitem__(index)
            return self._get_object(elto)

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"<Neo4j %s: %s>" % (self.__class__.__name__,
                                    self._class.__name__)

    def __contains__(self, value):
        if isinstance(value, Base) and hasattr(value, "url"):
            if self._attribute:
                return value.url in [elto[self._attribute]
                                     for elto in self._list]
            else:
                return value.url in self._list
        return False

    def __iter__(self):
        return self

    def next(self):
        if self._index == 0:
            raise StopIteration
        self._index = self._index - 1
        return self.__getitem__(self._index)

class NodesProxy(dict):
    """
    Class proxy for node in order to allow get a node by id and
    create new nodes through calling.
    """

    def __init__(self, node, reference_node=None, node_index=None):
        self._node = node
        self._reference_node = reference_node
        self._node_index = node_index

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
            if isinstance(key, (str, unicode)) and key.startswith(self._node):
                return tx.subscribe(TX_GET, key, obj=self)
            else:
                return tx.subscribe(TX_GET, "%s/%s/" % (self._node, key), obj=self)
        else:
            if isinstance(key, (str, unicode)) and key.startswith(self._node):
                return Node(key)
            else:
                return Node("%s/%s/" % (self._node, key))

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
                kwargs.pop("tx", None)
            return tx.subscribe(TX_POST, self._node, data=kwargs, obj=self)
        else:
            return Node(self._node, create=True, data=kwargs)

    def delete(self, key, tx=None):
        tx = Transaction.get_transaction(tx)
        if tx:
            return self.__getitem__(key, tx=tx)
        else:
            node = self.__getitem__(key)
            del node

    def _indexes(self):
        if self._node_index:
            return IndexesProxy(self._node_index, NODE)
    indexes = property(_indexes)

class Node(Base):
    """
    Node class.
    """

    def __init__(self, url, *args, **kwargs):
        kwargs['request_builder'] = NodeRequestBuilder(url)
        super(Node, self).__init__(url, *args, **kwargs)

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
            create_relationship_url = self._dic.create_relationship_url()
            data = {
                "to": to.url,
                "type": relationship_name,
            }
            if "tx" in kwargs and isinstance(kwargs["tx"], Transaction):
                x = kwargs.pop("tx", None)
                del x  # Makes pyflakes happy
            if kwargs:
                data.update({"data": kwargs})
            if tx:
                return tx.subscribe(TX_POST, create_relationship_url,
                                    data=data, obj=self)
            response, content = Request().post(create_relationship_url,
                                               data=data)
            if response.status == 201:
                return Relationship(response.get("location"))
            elif response.status == 404:
                raise NotFoundError(response.status, "Node specified by the " \
                                                     "URI not of \"to\" node" \
                                                     "not found")
            else:
                raise StatusException(response.status, "Invalid data sent")
        return relationship

    # HACK: Special methods for handle pickling manually
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
        return Relationships(self)
    relationships = property(_get_relationships)

    def _get_id(self):
        return int(self.url.split("/")[-1])
    id = property(_get_id)

    def __hash__(self):
        return hash(self.id)

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
        if (paginated or page_size or time_out)\
            and "paged_traverse" in self._dic:
            traverse_url = self._dic.paged_traverse_url(returns,
                                                                    page_size,
                                                                    time_out)
            return PaginatedTraversal(traverse_url, returns, data=data)
        else:
            traverse_url = self._dic.traverse_url(returns)
            response, content = Request().post(traverse_url, data=data)
            if response.status == 200:
                results_list = json.loads(content)
                if returns == NODE:
                    return Iterable(Node, results_list, "self")
                elif returns == RELATIONSHIP:
                    return Iterable(Relationship, results_list, "self")
                elif returns == PATH:
                    return Iterable(Path, results_list, "self")
                elif returns == POSITION:
                    return Iterable(Position, results_list, "self")
            elif response.status == 404:
                raise NotFoundError(response.status, "Node or relationship " \
                                                     "not found")
            else:
                raise StatusException(response.status, "Invalid data sent")


class PaginatedTraversal(object):
    """
    Class for paged traversals.
    """

    def __init__(self, url, returns, data=None):
        self.url = url
        self.returns = returns
        self.data = data
        self._results = []
        response, content = Request().post(self.url, data=self.data)
        if response.status == 201:
            self._results = json.loads(content)
            self._next_url = response.get("location")
        else:
            self._next_url = None

    def __iter__(self):
        return self

    def next(self):
        if self._results:
            self._item = False
            if self.returns == NODE:
                results = Iterable(Node, self._results, "self")
            elif self.returns == RELATIONSHIP:
                results = Iterable(Relationship, self._results, "self")
            elif self.returns == PATH:
                results = Iterable(Path, self._results)
            elif self.returns == POSITION:
                results = Iterable(Position, self._results)
            self._results = []
            if self._next_url:
                response, content = Request().get(self._next_url)
                if response.status == 200:
                    self._results = json.loads(content)
                    self._next_url = response.get("location")
                else:
                    self._next_url = None
            return results
        else:
            raise StopIteration


class IndexesProxy(dict):
    """
    Class proxy for indexes (nodes and relationships).
    """

    def __init__(self, index_url, index_for=NODE):
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
        return unicode(self._dict)

    def _get_dict(self):
        indexes_dict = {}
        response, content = Request().get(self.url)
        if response.status == 200:
            indexes_dict = json.loads(content)
            for index_name, index_properties in indexes_dict.items():
                index_props = {}
                for key, val in index_properties.items():
                    index_props[str(key)] = val
                indexes_dict[index_name] = Index(self._index_for, index_name,
                                                 **index_props)
            return indexes_dict
        elif response.status == 404:
            raise NotFoundError(response.status, "Indexes not found")
        elif response.status == 204:
            return indexes_dict
        else:
            raise StatusException(response.status,
                                  "Error requesting indexes with GET %s" \
                                   % self.url)

    def create(self, name, **kwargs):
        data = {
            'name': name,
            'config': {
                'type': kwargs.get("type", INDEX_FULLTEXT),
                'provider': kwargs.get("provider", "lucene"),
            }
        }

        if name not in self._dict:
            tx = Transaction.get_transaction(kwargs.get("tx", None))
            if tx:
                if "tx" in kwargs and isinstance(kwargs["tx"], Transaction):
                    kwargs.pop("tx", None)
                callback = lambda new_obj: self._dict.update({name:new_obj})
                return tx.subscribe(TX_POST, self.url, data=data, obj=self,
                                    callback=callback)
            else:
                response, content = Request().post(self.url, data=data)
                if response.status == 201:
                    loaded_dict = json.loads(content)
                    result_dict = {}
                    for key, val in loaded_dict.items():
                        result_dict[str(key)] = val
                    self._dict[name] = Index(self._index_for, name, **result_dict)
                else:
                    raise StatusException(response.status, "Invalid data sent")
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


class Index(object):
    """
    key/value indexed lookups. Create an index object with GraphDatabase.index.
    The returned object supports dict style lookups, eg index[key][value].
    """
    #TODO Abstracting url building could be done here, as well. -@mhluongo
    @staticmethod
    def _get_results(url, node_or_rel, **kwargs):
        tx = Transaction.get_transaction(kwargs.get("tx", None))
        if tx:
            if "tx" in kwargs and isinstance(kwargs["tx"], Transaction):
                kwargs.pop("tx", None)
            return tx.subscribe(TX_GET, url)
        else:
            response, content = Request().get(url)
            if response.status == 200:
                data_list = json.loads(content)
                if node_or_rel == NODE:
                    return Iterable(Node, data_list, "self")
                else:
                    return Iterable(Relationship, data_list, "self")
            elif response.status == 404:
                raise NotFoundError(response.status,
                                    "Node or relationship not found")
            else:
                raise StatusException(response.status,
                                        "Error requesting index with GET %s" \
                                        % url)

    class IndexKey(object):
        """
        Intermediate object so that lookups can be done like:
        index[key][value]

        Lookups are formated as http://.../{index_name}/{key}/{value}, so this
        is the object that gets returned by index[key]. The REST request will
        be sent when the value is specified.
        """

        def __init__(self, index_for, url):
            self._index_for = index_for
            if url[-1] == '/':
                url = url[:-1]
            self.url = url

        def __getitem__(self, value):
            return self._get(value)

        def _get(self, value, tx=None):
            url = "%s/%s" % (self.url, smart_quote(value))
            return Index._get_results(url, self._index_for, tx=tx)

        def _set(self, value, item, **kwargs):
            # Neo4j hardly crush if you try to index a relationship in a
            # node index and viceversa.
            is_node_index = self._index_for == NODE and isinstance(item, Node)
            is_relationship_index = (self._index_for == RELATIONSHIP
                                     and isinstance(item, Relationship))
            if not (is_node_index or is_relationship_index):
                raise TypeError("%s is a %s and the index is for %ss"
                                % (item, self._index_for.capitalize(),
                                   self._index_for))
            value = smart_quote(value)
            if isinstance(item, Base):
                url_ref = item.url
            else:
                url_ref = item
            request_url = "%s/%s" % (self.url, value)

            tx = Transaction.get_transaction(kwargs.get("tx", None))
            if tx:
                if "tx" in kwargs and isinstance(kwargs["tx"], Transaction):
                    kwargs.pop("tx", None)
                return tx.subscribe(TX_POST, request_url, data=url_ref, obj=self)

            response, content = Request().post(request_url, data=url_ref)
            if response.status == 201:
                # Returns object that was indexed
                entity = json.loads(content)
                if self._index_for == NODE:
                    return Node(entity['self'], data=entity['data'])
                else:
                    return Relationship(entity['self'], data=entity['data'])
            else:
                raise StatusException(response.status,
                                      "Error requesting index with POST %s " \
                                      ", data %s" % (request_url, url_ref))

        def __setitem__(self, value, item):
            return self._set(value, item)

        def query(self, value):
            url = "%s?query=%s" % (self.url, smart_quote(value))
            return Index._get_results(url, self._index_for)

    def __init__(self, index_for, name, **kwargs):
        self._index_for = index_for
        self.name = name
        self.template = kwargs.get("template")
        self.provider = kwargs.get("provider")
        self.type = kwargs.get("type")
        url = self.template.replace("{key}/{value}", "")
        if url[-1] == '/':
            url = url[:-1]
        self.url = url

    @classmethod
    def from_url(cls, url, update_dict={}):
        init_kwargs = {}

        path = urlparse.urlparse(url).path
        if path[-1] == '/':
            path = path[:-1]
        _, path_type, path_name = path.rsplit('/',2)

        if 'name' in update_dict:
            name = update_dict['name']
        else:
            #infer name from url (should be last part of path)
            name = path_name
        # infer index type from url
        index_for = NODE
        if path_type == 'relationship':
            index_for = RELATIONSHIP

        init_kwargs.update(update_dict.get('body', {}))
        return cls(index_for, name, **init_kwargs)

    def __getitem__(self, key):
        return self.get(key)

    def __repr__(self):
        return self.__unicode__()

    def __eq__(self, other):
        return isinstance(other, Index) and self.url == other.url

    def __hash__(self):
        return hash(self.url)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"<Neo4j %s: %s>" % (self.__class__.__name__, self.url)

    def add(self, key, value, item, tx=None):
        self.get(key)._set(value, item, tx=tx)

    def get(self, key, value=None):
        key = smart_quote(key)
        if value:
            value = smart_quote(value)
            return self.IndexKey(self._index_for,
                                 "%s/%s" % (self.url, key))[value]
        else:
            return self.IndexKey(self._index_for, "%s/%s" % (self.url, key))

    def delete(self, key=None, value=None, item=None, **kwargs):
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
            elif key and not value:
                key = smart_quote(key)
                url = "%s/%s" % (self.template.replace("{key}/{value}", key),
                                 item.id)
            elif not key and not value:
                url = self.template.replace("{key}/{value}", item.id)
            else:
                raise TypeError("delete() takes at least 2 arguments, the " \
                                "key of the index and the %s to remove"
                                % self._index_for)
        tx = Transaction.get_transaction(kwargs.get("tx", None))
        if tx:
            if "tx" in kwargs and isinstance(kwargs["tx"], Transaction):
                kwargs.pop("tx", None)
            return tx.subscribe(TX_DELETE, url)
        else:
            response, content = Request().delete(url)
            if response.status == 404:
                if options.SMART_ERRORS:
                    raise KeyError(self._index_for.capitalize())
                else:
                    index_for = self._index_for.capitalize()
                    raise NotFoundError(response.status, "%s not found" % index_for)
            elif response.status != 204:
                raise StatusException(response.status)

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
            return self.get('text').query(str(query))
        else:
            key, query = args
            index_key = self.get(key)
            if isinstance(query, basestring):
                return index_key.query(query)
            else:
                if query.fielded:
                    raise ValueError('Queries with an included key should '\
                                     'not include a field.')
                return index_key.query(str(query))


class RelationshipsProxy(dict):
    """
    Class proxy for relationships in order to allow get a relationship by id
    and create new relationships through calling.
    """

    def __init__(self, relationship, relationship_index):
        self._relationship = relationship
        self._relationship_index = relationship_index

    def __getitem__(self, key, tx=None):
        tx = Transaction.get_transaction(tx)
        if tx:
            return tx.subscribe(TX_GET, "%s/%s" % (self._relationship, key),
                                obj=self)
        else:
            return Relationship("%s/%s" % (self._relationship, key))

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

    def _indexes(self):
        if self._relationship_index:
            return IndexesProxy(self._relationship_index, RELATIONSHIP)
    indexes = property(_indexes)


class Relationships(object):
    """
    Relationships class for a node.
    """

    def __init__(self, node):
        self._node = node
        self._pattern = "{-list|&|types}"
        self._dict = {}

    def __getattr__(self, relationship_type):

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
                    return tx.subscribe(TX_GET, url, obj=self)
                response, content = Request().get(url)
                if response.status == 200:
                    relationship_list = json.loads(content)
                    relationships = Iterable(Relationship, relationship_list,
                                             "self")
                    # relationships = [Relationship(r["self"])
                    #                  for r in relationship_list]
                    self._dict[relationship_type] = relationships
                    return self._dict[relationship_type]
                elif response.status == 404:
                    if options.SMART_ERRORS:
                        return []
                    else:
                        raise NotFoundError(response.status,
                                            "Node or relationship not found")
                else:
                    if options.SMART_ERRORS:
                        raise KeyError("Node not found")
                    else:
                        raise StatusException(response.status, "Node not found")
            raise NameError("name %s is not defined" % relationship_type)

        return get_relationships

    def __len__(self, tx=None):
        tx = Transaction.get_transaction(tx)
        if tx:
            return len(self.__getattr__("all")(tx=tx))
        elif "all" in self._dict:
            return len(self._dic["all"])
        else:
            return len(self.__getattr__("all")())

    def count(self, tx=None):
        return self.__len__(tx=tx)

    def __getitem__(self, index, tx=None):
        tx = Transaction.get_transaction(tx)
        return self.__getattr__("all")(tx=tx)[index]

    def create(self, relationship_name, to, **kwargs):
        # TODO: Improve the unicode checking
        try:
            return self._node._create_relationship(relationship_name)(to, **kwargs)
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
        return Node(self._dic['start'])
    start = property(_get_start)

    def _get_end(self):
        return Node(self._dic['end'])
    end = property(_get_end)

    def _get_type(self):
        return self._dic['type'].encode("utf8")
    type = property(_get_type)

    def _get_id(self):
        return int(self.url.split("/")[-1])
    id = property(_get_id)


class Path(object):
    """
    Path class for return type PATH in traversals.
    """

    def __init__(self, dic):
        self._dic = dic
        self._length = int(dic["length"])
        self._nodes = []
        self._relationships = []
        self._iterable = []
        self._start = Node(self._dic["start"])
        self._end = Node(self._dic["end"])
        for i in range(0, len(dic["relationships"])):
            node = Node(dic["nodes"][i])
            self._nodes.append(node)
            relationship = Relationship(dic["relationships"][i])
            self._relationships.append(relationship)
            self._iterable.append(node)
            self._iterable.append(relationship)
        node = Node(dic["nodes"][-1])
        self._nodes.append(node)
        self._iterable.append(node)

    def __len__(self):
        return self._length

    def __iter__(self):
        while True:
            for obj in self._iterable:
                yield obj

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
        return self._get_nodes
    nodes = property(_get_nodes)

    def _get_relationships(self):
        return self._relationships
    relationships = property(_get_relationships)


class Position(object):
    """
    Position class for return type POSITION in traversals.
    """

    def __init__(self, dic):
        self._node = Node(dic["node"])
        self._depth = int(dic["depth"])
        relationship = Relationship(dic.get("last relationship",
                                    dic.get("last_relationship", None)))
        self._last_relationship = relationship
        self._path = Path(dic["path"])

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

class ExtensionsProxy(dict):
    """
    Class proxy for extensions in order to allow get an extension by module
    and class name and executing with the right params through calling.
    """

    def __init__(self, extensions):
        self._extensions = extensions
        self._dict = {}

    def __getitem__(self, attr):
        return self.__getattr__(attr)

    def __getattr__(self, attr):
        if attr in self._dict:
            return self._dict[attr]
        class_name = self._extensions[attr]
        # Using an anonymous class
        return type("ExtensionModule", (dict, ), {
            '__str__': lambda self: self.__unicode__(),
            '__repr__': lambda self: self.__unicode__(),
            '__unicode__': lambda self: u"<Neo4j %s: %s>" \
                                        % (self.__class__.__name__,
                                           unicode(class_name.keys())),
            '__getitem__': lambda self, _attr: self.__getattr__(_attr),
            '__getattr__': lambda self, _attr: Extension(class_name[_attr]),
            'get': lambda self, _attr: self.__getattr__(_attr),
        })()

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        if not self._dict:
            self._dict = self._get_dict()
        return unicode(self._dict)

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


class Extension(object):
    """
    Extension class.
    """

    def __init__(self, url):
        self._dic = {}
        if url.endswith("/"):
            url = url[:-1]
        self.url = url
        response, content = Request().get(self.url)
        if response.status == 200:
            self._dic.update(json.loads(content).copy())
            self.description = self._dic['description']
            self.name = self._dic['name']
            self.extends = self._dic['extends']
            self.parameters = self._dic['parameters']
        else:
            raise NotFoundError(response.status, "Unable get extension")

    def __call__(self, *args, **kwargs):
        # The returns param is a temporary solution while
        # a proper way to get the data type of returned values by
        # the extensions is implemented in Neo4j
        returns = kwargs.pop("returns", None)
        parameters = self._parse_parameters(args, kwargs)
        response, content = Request().post(self.url, data=parameters)
        if response.status == 200:
            result = json.loads(content)
            # Another option is to inspect the results
            if not returns:
                if isinstance(result, (tuple, list)) and len(result) > 0:
                    returns = result[0].get("self", None)
                elif isinstance(result, dict) and "self" in result:
                    returns = result.get("self", None)
            if isinstance(result, (tuple, list)) and returns:
                if NODE in returns:
                    return Iterable(Node, result, "self")
                elif RELATIONSHIP in returns:
                    return Iterable(Relationship, result, "self")
                elif PATH in returns or FULLPATH in returns:
                    return Iterable(Path, result)
                elif POSITION in returns:
                    return Iterable(Position, result)
            if isinstance(result, dict) and returns:
                if NODE in returns:
                    return Node(result["self"], data=result)
                elif RELATIONSHIP in returns:
                    return Relationship(result["self"], data=result)
                elif PATH in returns:
                    return Path(result)
                elif POSITION in returns:
                    return Position(result)
            elif result:
                return result
            else:
                return []
        elif response.status == 404:
            raise NotFoundError(response.status, "Extension not found")
        else:
            raise StatusException(response.status, "Invalid data sent")

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
        required = [np for np in self.parameters if np["optional"] == False]
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


def smart_quote(val):
    # TODO: Improve the unicode checking
    try:
        safe_key = urllib.quote(val, safe="")
    except (KeyError, UnicodeEncodeError, UnicodeError):
        safe_key = urllib.quote(val.encode("utf8"), safe="")
    return safe_key

def deep_replace(seq_or_mapping, match, replacement):
    """
    Performs a string replace on all values in a collection, and returns a 
    copy of the collection. Note that while all containers will be copies of 
    the originally nested containers, non-str values will not be adjusted.

    In the case of a mapping, the keys are not adjusted- only the values.
    """
    #base case, if string
    if isinstance(seq_or_mapping, basestring):
        return set_or_mapping.replace(match, replacement) 
    elif hasattr(seq_or_mapping, 'items'):
        new_coll = {}
        for k, v in seq_or_mapping.items():
            new_coll[k] = deep_replace(v, match, replacement)
        return new_coll
    else:
        return [deep_replace(v, match, replacement) for v in seq_or_mapping]
