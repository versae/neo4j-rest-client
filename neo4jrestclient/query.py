# -*- coding: utf-8 -*-
# Inspired by: https://github.com/CulturePlex/Sylva
#                     /tree/master/sylva/engines/gdb/lookups
import json
import uuid
from collections import Sequence
import warnings

from neo4jrestclient.constants import RAW
from neo4jrestclient.request import Request
from neo4jrestclient.exceptions import StatusException, TransactionException
from neo4jrestclient.utils import text_type, string_types, in_ipnb


class BaseQ(object):
    # Based on: https://github.com/scholrly/lucene-querybuilder
    #                  /blob/master/lucenequerybuilder/query.py
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
                 nullable=None, var=u"n", **kwargs):
        self._and = None
        self._or = None
        self._not = None
        self.property = property
        self.lookup = lookup
        self.match = match
        self.nullable = nullable
        self.var = var
        if property and (not self.lookup or self.match is None):
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
        return ((self.property and self.lookup and self.match is not None) or
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

    def get_query_objects(self, var=None, prefix=None, params=None,
                          version=None):
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
            matchs = []
            for list_item in self.match:
                if isinstance(list_item, string_types):
                    item = self._escape(list_item)
                else:
                    item = list_item
                matchs.append(item)
            match = matchs
        elif self.lookup == "isnull":
            if self.match:
                lookup = u"is"
            else:
                lookup = u"is not"
            match = u"NULL"
        elif self.lookup in ["eq", "equals"]:
            lookup = u"="
            if isinstance(self.match, string_types):
                match = u"'{0}'".format(self._escape(self.match))
            else:
                match = self.match
        elif self.lookup in ["neq", "notequals"]:
            lookup = u"<>"
            if isinstance(self.match, string_types):
                match = u"'{0}'".format(self._escape(self.match))
            else:
                match = self.match
        else:
            lookup = self.lookup
            match = u""
        return lookup, match

    def get_query_objects(self, var=None, prefix=None, params=None,
                          version=None):
        if var:
            self.var = var
        if not params:
            params = {}
        if not prefix:
            prefix = u""
        else:
            params.update(params)
        if self._and is not None:
            left_and = self._and[0].get_query_objects(params=params,
                                                      version=version)
            params.update(left_and[1])
            right_and = self._and[1].get_query_objects(params=params,
                                                       version=version)
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
            op_not = self._not.get_query_objects(params=params,
                                                 version=version)
            params.update(op_not[1])
            query = u"NOT ( {0} )".format(op_not[0])
        elif self._or is not None:
            left_or = self._or[0].get_query_objects(params=params,
                                                    version=version)
            params.update(left_or[1])
            right_or = self._or[1].get_query_objects(params=params,
                                                     version=version)
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
            prop = text_type(self.property).replace(u"`", u"\\`")
            NEO4J_V2 = version and version.split(".")[0] >= "2"
            if not NEO4J_V2 and self.nullable is None:
                # Backwards compatibility for Neo5j versions prior 2.0
                self.nullable = True
            if self.lookup == 'isnull':
                query_format = ("{0}.`{1}` {2} NULL")
                query = query_format.format(self.var, prop, lookup)
            elif NEO4J_V2 and self.nullable is not None:
                warnings.warn("Deprecated, Neo4j +2.0.0 does not support "
                              "the use of 'nullable' ('!' and '?' operators).",
                              DeprecationWarning)
                if self.nullable is True:
                    try:
                        query_format = (u"(has({0}.`{1}`) and {2}.`{3}` "
                                        u"{4} {{{5}}})")
                        query = query_format.format(self.var, prop,
                                                    self.var, prop,
                                                    lookup, key)
                    except AttributeError:
                        query = (u"( has(%s.`%s`) and %s.`%s` %s {%s} )"
                                 % (self.var, prop, self.var, prop, lookup,
                                    key))
                elif self.nullable is False:
                    try:
                        query_format = (u"(not(has({0}.`{1}`)) or {2}.`{3}` "
                                        u"{4} {{{5}}})")
                        query = query_format.format(self.var, prop,
                                                    self.var, prop,
                                                    lookup, key)
                    except AttributeError:
                        query = (u"( not(has(%s.`%s`)) or %s.`%s` %s {%s} )"
                                 % (self.var, prop, self.var, prop, lookup,
                                    key))
            else:
                if NEO4J_V2:
                    nullable = u""
                elif self.nullable is True:
                    nullable = u"!"
                elif self.nullable is False:
                    nullable = u"?"
                else:
                    nullable = u""
                try:
                    query_format = u"{0}.`{1}`{2} {3} {{{4}}}"
                    query = query_format.format(self.var, prop, nullable,
                                                lookup, key)
                except AttributeError:
                    query = u"%s.`%s`%s %s {%s}" % (self.var, prop,
                                                    nullable, lookup, key)
            params[key] = match
        return query, params


class CypherException(Exception):
    pass


class QuerySequence(Sequence):

    def __init__(self, cypher, auth, q, params=None, types=None, returns=None,
                 lazy=False, tx=None):
        self.q = q
        self.params = params
        self.columns = None
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
        # Store rows and graphs information
        self._elements_row = None
        self._elements_graph = None
        if tx:
            tx.append(q=self.q, params=self.params, returns=self._returns,
                      obj=self)
            tx.execute()
        elif not lazy:
            self._get_elements()

    def _get_elements(self):
        if self._elements is None:
            response = self.get_response()
            try:
                self._elements = QuerySequence.cast(
                    self, elements=response["data"], returns=self._returns
                )
                self.columns = response.get("columns", None)
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

    def _repr_html_(self):
        return self.to_html()

    def to_html(self, title=None, width=None, height=None):
        html = self._plot_graph(
            self._elements_graph,
            title=title,
            width=width,
            height=height,
        )
        return html

    def _transform_graph_to_d3(self, graph):
        nodes = {}
        links = []
        links_ids = set()
        properties = set()
        for node_dict in graph:
            for node in node_dict.get('nodes', []):
                node_id = node.get('id', len(nodes))
                if node_id not in nodes:
                    node_properties = node.get('properties', {})
                    nodes.update({
                        node_id: {
                            'fill': 'white',
                            'id': node_id,
                            'label': node_id,
                            'properties': node_properties
                        }
                    })
                    properties.update(node_properties.keys())
            for relationship in node_dict.get('relationships', []):
                link_id = relationship.get('id', len(links_ids))
                if (link_id not in links_ids
                        and 'startNode' in relationship
                        and 'endNode' in relationship):
                    rel_properties = relationship.get('properties', {})
                    links.append({
                        'id': link_id,
                        'source': relationship.get('startNode'),
                        'stroke': 'black',
                        'target': relationship.get('endNode'),
                        'label': relationship.get('type'),
                        'properties': rel_properties,
                    })
                    links_ids.add(link_id)
                    # properties.add(*rel_properties.keys())
        d3_graph = {
            'directed': True,
            'graph': [],
            'multigraph': True,
            'links': links,
            'nodes': nodes,
            'properties': list(properties)
        }
        return d3_graph

    def _plot_graph(self, graph, title=None, width=None, height=None):
        """
        Return a HTML representation for a particular QuerySequence.
        Mainly for IPython Notebook.
        """
        if not self._elements_row and not self._elements_graph:
            raise ValueError('Unable to display the graph or the table')
        title = title or self.q
        width = width or json.dumps(None)
        height = height or 300
        d3_uuid = text_type(uuid.uuid1())
        d3_graph = self._transform_graph_to_d3(graph)
        d3_id = "d3_id_" + d3_uuid
        d3_title = title
        d3_container_id = d3_id + "_d3c"
        style = """
        #{d3_id} path.link {{
            fill: none;
            stroke-width: 1.5px;
        }}
        #{d3_id} .node {{
            /*fill: #ccc;*/
            stroke: #333;
            stroke-width: 1.5px;
        }}
        #{d3_id} text {{
            font: 10px sans-serif;
            pointer-events: none;
        }}
        #{d3_id} text.shadow {{
            stroke: #fff;
            stroke-width: 3px;
            stroke-opacity: .8;
        }}
        #{d3_id} .node.sticky {{
            /* stroke-width: 2px; */
        }}
        """.format(d3_id=d3_id)
        js = """
        var links = graph.links;
        var nodes = graph.nodes;

        // Compute the distinct nodes from the links.
        links.forEach(function(link) {
            link.source = (nodes[link.source] ||
                           (nodes[link.source] = {name: link.source}));
            link.target = (nodes[link.target] ||
                           (nodes[link.target] = {name: link.target}));
        });

        var w = width || $(container).width(), h = height;

        var force = d3.layout.force()
            .nodes(d3.values(nodes))
            .links(links)
            .size([w, h])
            .linkDistance(60)
            .charge(-300)
            .on("tick", tick)
            .start();

        var svg = d3.select(container).append("svg:svg")
            .attr("width", w)
            .attr("height", h);

        // Per-type markers, as they don't inherit styles.
        svg.append("svg:defs").selectAll("marker")
            .data(["arrow"])
            .enter().append("svg:marker")
            .attr("id", String)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 15)
            .attr("refY", -1.5)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("svg:path")
            .attr("d", "M0,-5L10,0L0,5");

        var path = svg.append("svg:g").selectAll("path")
            .data(force.links())
            .enter().append("svg:path")
            .attr("class", function(d) { return "link " + d.stroke; })
            .attr("stroke", function(d) { return d.stroke; })
            .attr("marker-end", function(d) { return "url(#arrow)"; });

        var circle = svg.append("svg:g").selectAll("circle")
            .data(force.nodes())
            .enter().append("svg:circle")
            .attr("fill", function(d) { return d.fill; })
            .attr("r", 6)
            .attr("class", "node")
            .call(force.drag)
            .on("mousedown", function(d) {
                d.fixed = true;
                d3.select(this).classed("sticky", true);
            });

        var text = svg.append("svg:g").selectAll("g")
            .data(force.nodes())
            .enter().append("svg:g");

        // A copy of the text with a thick white stroke for legibility.
        text.append("svg:text")
            .attr("x", 8)
            .attr("y", ".31em")
            .attr("class", "shadow")
            .text(function(d) { return d.label; });

        text.append("svg:text")
            .attr("x", 8)
            .attr("y", ".31em")
            .attr("class", "front")
            .text(function(d) { return d.label; });

        // Use elliptical arc path segments to doubly-encode directionality.
        function tick() {
            path.attr("d", function(d) {
                var dx = d.target.x - d.source.x,
                dy = d.target.y - d.source.y,
                dr = Math.sqrt(dx * dx + dy * dy);
                return ("M" + d.source.x + "," + d.source.y + "A"
                        + dr + "," + dr + " 0 0,1 " + d.target.x + ","
                        + d.target.y);
            });

            circle.attr("transform", function(d) {
                return "translate(" + d.x + "," + d.y + ")";
            });

            text.attr("transform", function(d) {
                return "translate(" + d.x + "," + d.y + ")";
            });
        }

        // Display options
        var display = $(container + "_display");
        graph.properties.forEach(function (property) {
            var option = $("<OPTION/>");
            option.text(property);
            option.attr("value", property);
            display.append(option);
        });
        display.on("change", function () {
            var selected = $(this).find(":selected").val(),
                displayFunc;
            if (selected.length !== 0) {
                displayFunc = function(d) {
                    return d.properties[selected];
                }
            } else {
                displayFunc = function(d) {
                    return d.label;
                }
            }
            text.select("text.front").text(displayFunc);
            text.select("text.shadow").text(displayFunc);
        });
        """
        return ("""
        <style type="text/css">
        {style}
        </style>

        <div class="accordion">
            <div class="accordion-group">
                <div class="accordion-heading">
                    <a class="accordion-toggle collapsed"
                       data-toggle="collapse" data-parent=""
                       href="#{d3_id}">
                        {d3_title}
                    </a>
                </div>
                <div id="{d3_id}" class="accordion-body in collapse">
                    <div class="accordion-inner">
                        <div id="{d3_container_id}">
                            <select id="{d3_container_id}_display">
                                <option value="">ID</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            var neo4jrestclient = window.neo4jrestclient || {{}};
            neo4jrestclient['{d3_uuid}'] = {{}};
            neo4jrestclient['{d3_uuid}'].graph = {d3_graph};
            neo4jrestclient['{d3_uuid}'].container_id = "{d3_container_id}";
            neo4jrestclient['{d3_uuid}'].container = "#{d3_container_id}";
            neo4jrestclient['{d3_uuid}'].render = function () {{
                (function (graph, container, width, height) {{
                    {js}
                }})(
                    neo4jrestclient['{d3_uuid}'].graph,
                    neo4jrestclient['{d3_uuid}'].container,
                    {width},
                    {height}
                );
            }}
            if (!window.d3) {{
                $.getScript(
                    "//d3js.org/d3.v2.js?2.9.1",
                    neo4jrestclient['{d3_uuid}'].render
                );
            }} else {{
                neo4jrestclient['{d3_uuid}'].render();
            }}
        </script>
        """.format(
            style=style,
            js=js,
            d3_graph=json.dumps(d3_graph),
            d3_id=d3_id,
            d3_uuid=d3_uuid,
            d3_title=d3_title,
            d3_container_id=d3_container_id,
            width=width,
            height=height,
        ))

    def get_response(self):
        # Preparing slicing and ordering
        q = self.q
        params = self.params
        version = self._auth.get('version', None)
        NEO4J_V2 = version and version.split(".")[0] >= "2"
        if self._order_by:
            orders = []
            for o, order in enumerate(self._order_by):
                order_key = "_order_by_%s" % o
                if order_key not in params:
                    if NEO4J_V2:
                        orders.append(u"n.`{%s}` %s"
                                      % (order_key, order[1]))
                    else:
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
        response = Request(**self._auth).post(self._cypher, data=data)
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        elif response.status_code == 400:
            err_msg = u"Cypher query exception"
            try:
                err_msg = "%s: %s" % (err_msg, response.json()["message"])
            except:
                err_msg = "%s: %s" % (err_msg, response.text)
            raise CypherException(err_msg)
        else:
            raise StatusException(response.status_code, "Invalid data sent")

    @staticmethod
    def cast(cls, elements, returns=None, types=None, auth=None, cypher=None):
        if types is None:
            types = cls._types
        if auth is None:
            auth = cls._auth
        if cypher is None:
            cypher = cls._cypher
        neutral = lambda x: x
        # For IPython Notebook
        cls._elements_row = []
        cls._elements_graph = []
        if not returns or returns is RAW:
            if len(elements) > 0:
                results = []
                for element in elements:
                    # For IPython Notebook
                    if "row" in element:
                        cls._elements_row.append(element["row"])
                    if "graph" in element:
                        cls._elements_graph.append(element["graph"])
                    # For transactional Cypher endpoint
                    results.append(element.get("rest", None))
                return results
            else:
                return elements
        else:
            results = []
            if not isinstance(returns, (tuple, list)):
                returns = [returns]
            else:
                returns = list(returns)
            for row in elements:
                # For IPython Notebook
                if "row" in row:
                    cls._elements_row.append(row["row"])
                if "graph" in row:
                    cls._elements_graph.append(row["graph"])
                # For transactional Cypher endpoint
                if "rest" in row:
                    row = row["rest"]
                # We need both list to have the same lenght
                len_row = len(row)
                len_returns = len(returns)
                if len_row > len_returns:
                    returns += [neutral] * (len_row - len_returns)
                returns = returns[:len_row]
                # And now, apply i-th function to the i-th column in each row
                casted_row = []
                types_keys = types.keys()
                for i, element in enumerate(row):
                    # if "rest" in element:
                    #     element = element["rest"]
                    func = returns[i]
                    # We also allow the use of constants like NODE, etc
                    if isinstance(func, string_types):
                        func_lower = func.lower()
                        if func_lower in types_keys:
                            func = types[func_lower]
                    if func in (types.get("node", ""),
                                types.get("relationship", "")):
                        obj = func(element["self"], update_dict=element,
                                   auth=auth, cypher=cypher)
                        casted_row.append(obj)
                    elif func in (types.get("path", ""),
                                  types.get("position", "")):
                        obj = func(element, auth=auth, cypher=cypher)
                        casted_row.append(obj)
                    elif func in (None, True, False):
                        sub_func = lambda x: x is func
                        casted_row.append(sub_func(element))
                    else:
                        casted_row.append(func(element))
                if cls is not None and cls._return_single_rows:
                    results.append(*casted_row)
                else:
                    results.append(casted_row)
            return results


class QueryTransaction(object):
    """
    Transaction class for tge Cypher endpoint.
    """

    def __init__(self, cls, transaction_id, types, commit=True, update=True,
                 rollback=True, execute=False):
        self._class = cls
        self.url_begin = self._class._transaction
        self.url_tx = None
        self.url_commit = None
        self.id = transaction_id
        self.finished = False
        self._types = types
        self.auto_commit = commit
        self.auto_update = update
        self.auto_rollback = rollback
        self.auto_execute = execute
        self.statements = []
        self.references = []
        self.executed = []
        self.expires = None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if not self.finished:
            if self.auto_commit:
                self.commit()
            if isinstance(value, TransactionException) and self.auto_rollback:
                self.rollback()
        return True

    def _manage_errors(self, errors):
        message = u""
        if errors:
            for error in errors:
                message = u"{}\n{}:\n{}\n".format(
                    message, error["code"], error["message"]
                )
            raise TransactionException(200, message)

    def _begin(self):
        response = self._request(self.url_begin)
        content = response.json()
        self._manage_errors(content["errors"])
        self.url_tx = response.headers.get("location")
        self.url_commit = content["commit"]
        self.expires = content["transaction"]["expires"]

    def _request(self, url, statements=None):
        if statements is None:
            statements = []
        request = Request(**self._class._auth)
        data = {
            "statements": statements
        }
        response = request.post(url, data=data)
        if response.status_code in [200, 201]:
            return response
        else:
            raise TransactionException(response.status_code)

    def _execute(self, url, results=True):
        response = self._request(url, statements=self.statements)
        content = response.json()
        self._manage_errors(content["errors"])
        _results = self._update(content["results"])
        self.executed = self.references
        self.statements = []
        self.references = []
        if results:
            return _results

    def _update(self, result_list):
        if self.auto_update:
            results = []
            for i, result in enumerate(result_list):
                reference = self.references[i]
                obj = reference["obj"]
                returns = reference["returns"]
                statement = reference["statement"]
                if obj is None:
                    obj = QuerySequence(
                        q=statement['statement'],
                        params=statement['parameters'], returns=returns,
                        types=self._types, auth=self._class._auth,
                        cypher=self._class._cypher, lazy=True
                    )
                obj._elements = QuerySequence.cast(
                    obj, elements=result["data"], returns=returns
                )
                obj.columns = result.get("columns", None)
                results.append(obj)
            return results
        else:
            return result_list

    def append(self, q, params=None, returns=None, obj=None):
        result_data_contents = ["REST"]
        if in_ipnb():
            result_data_contents += ["row", "graph"]
        statement = {
            "statement": q,
            "parameters": params,
            "resultDataContents": result_data_contents,
        }
        self.statements.append(statement)
        self.references.append({
            "statement": statement,
            "returns": returns,
            "obj": obj,
        })

    def reset(self):
        if not self.url_tx:
            self._begin()
        response = self._request(self.url_tx)
        content = response.json()
        self._manage_errors(content["errors"])
        self.expires = content["transaction"]["expires"]
        return self.expires

    def execute(self):
        if self.auto_execute:
            self.url_commit = None
            return self.commit()
        if not self.url_tx:
            self._begin()
        results = self._execute(self.url_tx, results=True)
        self.finished = False
        return results

    def commit(self):
        if self.url_commit:
            url = self.url_commit
        else:
            url = u"{}/commit".format(self.url_begin)
        results = self._execute(url, results=True)
        self.finished = True
        return results

    def rollback(self):
        if self.url_tx:
            request = Request(**self._class._auth)
            response = request.delete(self.url_tx)
            if response.status_code in [200, 201]:
                self._manage_errors(response.json()["errors"])
                self.finished = True
                for reference in self.executed:
                    obj = reference["obj"]
                    if obj is not None:
                        obj._elements = []
                        obj.columns = None
                self.executed = []
            else:
                raise TransactionException(response.status_code)


class FilterSequence(QuerySequence):

    def __init__(self, cypher, auth, start=None, matches=None, lookups=[],
                 order_by=None, types=None, returns=None):
        self.version = auth.get('version', None)
        start = start or u"node(*)"
        q = u"start n=%s " % start
        if matches:
            if not isinstance(matches, (list, tuple)):
                matches = [matches]
            match = u", ".join(matches)
            q = u"{} match {}".format(q, match)
        where = None
        params = {}
        if lookups:
            wheres = Q()
            for lookup in lookups:
                if isinstance(lookup, Q):
                    wheres &= lookup
                elif isinstance(lookup, dict):
                    wheres &= Q(**lookup)
            where, params = wheres.get_query_objects(var="n",
                                                     version=self.version)
        if where:
            q = u"{} where {} return n ".format(q, where)
        else:
            q = u"{} return n ".format(q)
        super(FilterSequence, self).__init__(cypher=cypher, auth=auth, q=q,
                                             params=params, types=types,
                                             returns=returns, lazy=True)
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
