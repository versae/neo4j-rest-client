# -*- coding: utf-8 -*-
# Inspired by: https://github.com/CulturePlex/Sylva/tree/master/sylva/engines/gdb/lookups
import json
from collections import Sequence

from constants import RAW
from request import Request, StatusException


class BaseQ(object):
    # Based on: https://github.com/scholrly/lucene-querybuilder/blob/master/lucenequerybuilder/query.py
    """
    Q is a query builder for the Neo4j Cypher language backend

    It allows to build filters like
    Q("Artwork title", istartswith="copy", nullable=False)
    Q(property="Artwork title", lookup="istartswith", match="copy")
    """

    matchs = ("exact", "iexact",
              "contains", "icontains",
              "startswith", "istartswith",
              "endswith", "iendswith",
              "regex", "iregex",
              "gt", "gte", "lt", "lte",
              "in", "inrange", "isnull",
              "eq", "equals", "neq", "notequals")

    def __init__(self, property=None, lookup=None, match=None,
                 nullable=True, var=u"n", **kwargs):
        self._and = None
        self._or = None
        self._not = None
        self.property = property
        self.lookup = lookup
        self.match = match
        self.nullable = nullable
        self.var = var
        if property and (not self.lookup or not self.match):
            for m in self.matchs:
                if m in kwargs:
                    self.lookup = m
                    self.match = kwargs[m]
                    break
            else:
                all_matchs = ", ".join(self.matchs)
                raise ValueError("Q objects must have at least a lookup method"
                                 " (%s) and a match case".format(all_matchs))

    def is_valid(self):
        return ((self.property and self.lookup and self.match) or
                (self._and or self._or or self._not))

    def _make_and(q1, q2):
        q = q1.__class__()
        q._and = (q1, q2)
        return q

    def _make_not(q1):
        q = q1.__class__()
        q._not = q1
        return q

    def _make_or(q1, q2):
        q = q1.__class__()
        q._or = (q1, q2)
        return q

    def __and__(self, other):
        return BaseQ._make_and(self, other)

    def __or__(self, other):
        return BaseQ._make_or(self, other)

    def __invert__(self):
        return BaseQ._make_not(self)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((self.property, self.lookup, self.match,
                     self.nullable))

    def get_query_objects(self, var=None, prefix=None, params=None):
        """
        :return query, params: Query string and a dictionary for lookups
        """
        raise NotImplementedError("Method has to be implemented")

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        query, params = self.get_query_objects()
        return query.format(**params)


class Q(BaseQ):

    def _escape(self, s):
        return s

    def _get_lookup_and_match(self):
        if self.lookup == "exact":
            lookup = u"="
            match = u"{0}".format(self.match)
        elif self.lookup == "iexact":
            lookup = u"=~"
            match = u"(?i){0}".format(self.match)
        elif self.lookup == "contains":
            lookup = u"=~"
            match = u".*{0}.*".format(self.match)
        elif self.lookup == "icontains":
            lookup = u"=~"
            match = u"(?i).*{0}.*".format(self.match)
        elif self.lookup == "startswith":
            lookup = u"=~"
            match = u"{0}.*".format(self.match)
        elif self.lookup == "istartswith":
            lookup = u"=~"
            match = u"(?i){0}.*".format(self.match)
        elif self.lookup == "endswith":
            lookup = u"=~"
            match = u".*{0}".format(self.match)
        elif self.lookup == "iendswith":
            lookup = u"=~"
            match = u"(?i).*{0}".format(self.match)
        elif self.lookup == "regex":
            lookup = u"=~"
            match = u"{0}".format(self.match)
        elif self.lookup == "iregex":
            lookup = u"=~"
            match = u"(?i){0}".format(self.match)
        elif self.lookup == "gt":
            lookup = u">"
            match = self.match
        elif self.lookup == "gte":
            lookup = u">="
            match = self.match
        elif self.lookup == "lt":
            lookup = u"<"
            match = self.match
        elif self.lookup == "lte":
            lookup = u"<="
            match = self.match
        elif self.lookup in ["in", "inrange"]:
            lookup = u"IN"
            match = u"['{0}']".format(u"', '".join([self._escape(m)
                                      for m in self.match]))
        elif self.lookup == "isnull":
            if self.match:
                lookup = u"="
            else:
                lookup = u"<>"
            match = u"null"
        elif self.lookup in ["eq", "equals"]:
            lookup = u"="
            match = u"'{0}'".format(self._escape(self.match))
        elif self.lookup in ["neq", "notequals"]:
            lookup = u"<>"
            match = u"'{0}'".format(self._escape(self.match))
        else:
            lookup = self.lookup
            match = u""
        return lookup, match

    def get_query_objects(self, var=None, prefix=None, params=None):
        if var:
            self.var = var
        if not params:
            params = {}
        if not prefix:
            prefix = u""
        else:
            params.update(params)
        if self._and is not None:
            left_and = self._and[0].get_query_objects(params=params)
            params.update(left_and[1])
            right_and = self._and[1].get_query_objects(params=params)
            params.update(right_and[1])
            if self._and[0].is_valid() and self._and[1].is_valid():
                query = u"( {0} AND {1} )".format(left_and[0], right_and[0])
            elif self._and[0].is_valid() and not self._and[1].is_valid():
                query = u" {0} ".format(left_and[0])
            elif not self._and[0].is_valid() and self._and[1].is_valid():
                query = u" {0} ".format(right_and[0])
            else:
                query = u" "
        elif self._not is not None:
            op_not = self._not.get_query_objects(params=params)
            params.update(op_not[1])
            query = u"NOT ( {0} )".format(op_not[0])
        elif self._or is not None:
            left_or = self._or[0].get_query_objects(params=params)
            params.update(left_or[1])
            right_or = self._or[1].get_query_objects(params=params)
            params.update(right_or[1])
            if self._or[0].is_valid() and self._or[1].is_valid():
                query = u"( {0} OR {1} )".format(left_or[0], right_or[0])
            elif self._or[0].is_valid() and not self._or[1].is_valid():
                query = u" {0} ".format(left_or[0])
            elif not self._or[0].is_valid() and self._or[1].is_valid():
                query = u" {0} ".format(right_or[0])
            else:
                query = u" "
        else:
            query = u""
            lookup, match = self._get_lookup_and_match()
        if self.property is not None and self.var is not None:
            key = u"{0}p{1}".format(prefix, len(params))
            property = unicode(self.property).replace(u"`", u"\\`")
            if self.nullable is True:
                nullable = u"!"
            elif self.nullable is False:
                nullable = u"?"
            else:
                nullable = u""
            params[key] = match
            try:
                query_format = u"{0}.`{1}`{2} {3} {{{4}}}"
                query = query_format.format(self.var, property, nullable,
                                            lookup, key)
            except AttributeError:
                query = u"%s.`%s`%s %s {%s}" % (self.var, property, nullable,
                                                lookup, key)
        return query, params


class CypherException(Exception):
    pass


class QuerySequence(Sequence):

    def __init__(self, cypher, auth, q, params=None, types=None, returns=None):
        self.q = q
        self.params = params
        self._skip = None
        self._limit = None
        self._order_by = None
        self._returns = returns
        self._return_single_rows = False
        self._auth = auth
        self._cypher = cypher
        # This way we avoid a circular reference, by passing objects like Node
        self._types = types or {}
        self._elements = None

    def _get_elements(self):
        if self._elements is None:
            response = self.get_response()
            try:
                self._elements = self.cast(elements=response["data"],
                                           returns=self._returns)
            except:
                self._elements = response
        return self._elements
    elements = property(_get_elements)

    def __getitem__(self, key):
        return self.elements[key]

    def __contains__(self, item):
        return item in self.elements

    def __iter__(self):
        return (e for e in self.elements)

    def __len__(self):
        return len(self.elements)

    def __reversed__(self):
        return reversed(self.elements)

    def get_response(self):
        # Preparing slicing and ordering
        q = self.q
        params = self.params
        if self._order_by:
            orders = []
            for o, order in enumerate(self._order_by):
                order_key = "_order_by_%s" % o
                if order_key not in params:
                    nullable = ""
                    if len(order) == 3:
                        if order[2] is True:
                            nullable = "!"
                        elif order[2] is False:
                            nullable = "?"
                    orders.append(u"n.`{%s}`%s %s" % (order_key, nullable,
                                                      order[1]))
                    params[order_key] = order[0]
            if orders:
                q = u"%s order by %s" % (q, ", ".join(orders))
        # Lazy slicing
        if isinstance(self._skip, int) and "_skip" not in params:
            q = u"%s skip {_skip} " % q
            params["_skip"] = self._skip
        if isinstance(self._limit, int) and "_limit" not in params:
            q = u"%s limit {_limit} " % q
            params["_limit"] = self._limit
        # Making the real resquest
        data = {
            "query": q,
            "params": params,
        }
        response, content = Request(**self._auth).post(self._cypher, data=data)
        if response.status == 200:
            response_json = json.loads(content)
            return response_json
        elif response.status == 400:
            err_msg = u"Cypher query exception"
            try:
                err_msg = "%s: %s" % (err_msg, json.loads(content)["message"])
            except:
                err_msg = "%s: %s" % (err_msg, content)
            raise CypherException(err_msg)
        else:
            raise StatusException(response.status, "Invalid data sent")

    def cast(self, elements, returns=None):
        neutral = lambda x: x
        if not returns or returns is RAW:
            return elements
        else:
            results = []
            if not isinstance(returns, (tuple, list)):
                returns = [returns]
            else:
                returns = list(returns)
            for row in elements:
                # We need both list to have the same lenght
                len_row = len(row)
                len_returns = len(returns)
                if len_row > len_returns:
                    returns += [neutral] * (len_row - len_returns)
                returns = returns[:len_row]
                # And now, apply i-th function to the i-th column in each row
                casted_row = []
                types_keys = self._types.keys()
                for i, element in enumerate(row):
                    func = returns[i]
                    # We also allow the use of constants like NODE, etc
                    if isinstance(func, basestring):
                        func_lower = func.lower()
                        if func_lower in types_keys:
                            func = self._types[func_lower]
                    if func in (self._types["node"],
                                self._types["relationship"]):
                        obj = func(element["self"], data=element,
                                   auth=self._auth)
                        casted_row.append(obj)
                    elif func in (self._types["path"],
                                  self._types["position"]):
                        obj = func(element, auth=self._auth)
                        casted_row.append(obj)
                    elif func in (None, True, False):
                        sub_func = lambda x: x is func
                        casted_row.append(sub_func(element))
                    else:
                        casted_row.append(func(element))
                if self._return_single_rows:
                    results.append(*casted_row)
                else:
                    results.append(casted_row)
            return results


class FilterSequence(QuerySequence):

    def __init__(self, cypher, auth, start=None, lookups=[],
                 order_by=None, types=None, returns=None):
        start = start or u"node(*)"
        q = u"start n=%s " % start
        where = None
        params = {}
        if lookups:
            wheres = Q()
            for lookup in lookups:
                if isinstance(lookup, Q):
                    wheres &= lookup
                elif isinstance(lookup, dict):
                    wheres &= Q(**lookup)
            where, params = wheres.get_query_objects(var="n")
        if where:
            q = u"%s where %s return n " % (q, where)
        else:
            q = u"%s return n " % q
        super(FilterSequence, self).__init__(cypher=cypher, auth=auth, q=q,
                                             params=params, types=types,
                                             returns=returns)
        self._return_single_rows = True

    def __getitem__(self, key):
        if isinstance(key, slice):
            self._skip = key.start
            self._limit = key.stop
        return super(FilterSequence, self).__getitem__(key)

    def order_by(self, property=None, type=None, nullable=True, *args):
        if property is None and isinstance(args, (list, tuple)):
            self._order_by = args
        else:
            self._order_by = [(property, type, nullable)]
        return self
