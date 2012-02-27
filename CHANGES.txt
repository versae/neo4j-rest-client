Changes
=======

1.6.0 (2012-02-27)
------------------
- Adding documentation site.
- Finishing the experimental support for indexing and transactions.
- Adding preliminar indexing support in trasnsactions.
- Adding a new way to traverse the graph based on python-embedded.
- Removing __credits__ in favor of AUTHORS file. Updating version number.
- Fixes #33. Deprecating the requirement of a reference node.
- Added methods to bring it in line with the embedded driver.
- Added .single to Iterable and .items() to Node to bring it into alignment
  with the embedded driver.
- Adding non-functional realtionshos creation inside transactions.
- New returnable type "RAW", added in constants. Very useful for Gremlin and
  Cypher queries.
- Extensions can now return raw results. Fixes #52.
- Added a test for issue #52, returns=RAW.
- Adding relationships support to transactions.
- Fixes #49. Usage in extensions.
- Improving transaction support. Related #49.
- Fixing some PEP08 warnings.
- Fixes #43. Unable to reproduce the error.
- Fixes #49. Improving the batch efficiency in get requests.
- Fixes #47. Improving Paths management in traversals.
- Adding 'content-location' as possible header in responses instead of
  just 'location'.
- Fixing an error wwhen the value of a set property operation is None.
- Merge branch 'master' of github.com:versae/neo4j-rest-client into devel.
- Fix for paginated traversals under Neo4j 1.5.
- Added check for 'content-location' header in PaginatedTraversal, ensuring
  traversals don't stop early with Neo4j 1.5.


1.5.0 (2011-10-31)
------------------
- Removing the smart_quote function from indexing. It's not needed anymore with
  the new way to add elements to indices.
- Fixes #37.
- Using JSON object to set index key and value.


1.4.5 (2011-09-15)
------------------
- Adding more testing to returns parameter in the extensions.
- Fixes 32. It needs some more testing, maybe.
- Updated to using lucene-querybuilder 0.1.5 (bugfixes and better wildcard support).
- Fixed the test issue found in #34, and updated the REST client to using lucene-querybuilder 0.1.5.
- Fixes #34. Fixing dependency of lucene-querybuilder version
- Fixes #30. Fixing an issue deleting all index entries for a node.
- Fixing an issue with parameters in extensions.
- Ensure that self.result is always present on the object, even if it's None.
- Fixing naming glitch in exception message
- Ensure that self.result is always present on the object, even if it's None
- Fixing an error retrieving relationships in paths.
- Fixing an error in extensions, Path and Position.


1.4.4 (2011-08-17)
------------------
- Merge pull request #28 from mhluongo/master
- Made the DeprecationWarnings a bit more specific.
- Nodes can now be used in set and as dict keys, differentiated by id.
- Added a test for node hashing on id.
- Removed the 'Undirected' reference from tests to avoid a DepreactionWarning.
- Moved the relationship creation DeprecationWarning so creating a relationship
  the preferred way won't raise it.
- Got rid of the DeprecationWarning on import- moved in to whenever using
  Undirected.*.
- Fixed traversal return filters.
- Enabled return filters, including those with custom javascript bodies.
  Eventually a more elegant (Python instead of string based) solution for
  return filter bodies is in order.
- Fixed a mispelling in the test_traversal_return_filter case.
- Added a test for builtin and custom traversal return filters.
- Small bug fix for traversal
- Fixed bug in traverse method for POSITION and PATH return types.


1.4.3 (2011-07-28)
------------------
- Added some deprecation warnings.
- Added support for pickling ans some tests.
- Fixed an error deleting nodes and relationships on transactions.
- Finishied and refactored the full unicode support.


1.4.2 (2011-07-18)
------------------
- Updated the documentation and version.
- Added support for indices deletion.
- Improved Unicode support in properties keys and values and relationships
  types. Adding some tests.


1.4.1 (2011-07-12)
------------------
- Fixed an error retrieving relationships by id.
- Added control to handle exceptions raised by Request objects.
- Updated changes, manifest and readme files.


1.4.0 (2011-07-11)
------------------
- Updated version number for the new release.
- Updated documentation.
- Updated develpment requirements.
- Added support for paginated traversals.
- Passed pyflakes and PEP8 on tests.
- Added weight to Path class.
- Index values now quoted_plus.
- Changed quote to quote_plus for index values.
- Added two tests for unicode and url chars in index values.
- Added initial documentacion for transactions.
- Added the transaction support and several tests.
- Fixed the implementation of __contains__ in Iterable class for evaluation
  of 'in' and 'not in' expressions.
- Added documentation for Iterable objects.
- Added more transactions features.
- Added requirements file for virtual environments in development.
- Improved number of queries slicing the returned objects in a Iterable
  wrapper class.
- Added Q syntax for more complicated queries.
- Added support for the Q query syntax for indexes using the DSL
  at http://github.com/scholrly/lucene-querybuilder
- Fixed an error in the test_query_index case (forgot to include an 'or'.
  between queries).
- Added lucene-querybuilder to the test requirements in setup.py.
- Added a test case for Q-based queries.


1.3.4 (2011-06-22)
------------------
- Fixed the setup.py and httplib2 import error during installing.
- Reordered the options variables in an options.py file.
  Allows index.query() to be called with or without a key
- Fixed issue #15 regarding dependency to httplib2
- Patched index.query() so it can take a query without a key (to support, say,
  mutli-field Lucene queries). Ultimately, query so probably be refactored to
  Index (instead of IndexKey) because IndexKey doesn't actually help with
  full-text queries.
- Fixed for issue #19 (missed that urllib.quote).
- Altered the test_query_index case to reflect how I think indexing should
  work.
- Using assertTrue instead of failUnless in tests.py, failUnless is deprecated
  in 2.7 and up, so I figured we might as well switch.
- Added SMART_ERRORS (aka "Django mode"). If you set SMART_ERROR to True it
  will make the client throw KeyError instead of NotFoundError when a key is
  missing.


1.3.3 (2011-06-14)
------------------
- Fixed an introspection when the results list of a traverse is empty.
- Merge pull request #17 from mhluongo/master
- Resolved the STOP_AT_END_OF_GRAPH traversal test case.
  Calling .traverse(stop=STOP_AT_END_OF_GRAPH) will now traverse the graph
  without a max depth (and without 500 errors).
- Added a failing test case for traverse(stop=STOP_AT_END_OF_GRAPH).


1.3.2 (2011-05-30)
------------------
- Added a test for deleting relationships.
- Fixing an Index compatibility issue with Python 2.6.1.
- Fixing an error in extensions support with named params.


1.3.1 (2011-04-16)
------------------
- Fixing setup.py.


1.3.0 (2011-04-15)
------------------
- First Python Index Package release with full support for Neo4j 1.3.
