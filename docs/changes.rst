Changes
=======

2.0.4 (2014-06-20)
------------------
- Typos
- Bugfixes
- Drop support for 1.6 branch


2.0.3 (2014-05-16)
------------------
- Update travis to test Neo4j versions 1.9.7 and 2.0.3
- Fix #104. Keep backwards compatibility for 'nullable' prior 2.0
  It will be deprecated for Neo4j>=2.0.0
- Update Q class for nullable=True
- Fix un/pickling extenions
- Refactorize get auth information from the connection URL
- Update queries.rst (typo)
- Fix the lazy loading of extensions


2.0.2 (2014-04-04)
------------------
- Add Pickle support for GraphDatabase objects
- Add small control to change display property in IPython
- Add a new parameter to auto_execute transactions in one single request
- Fix auto transaction in Cypher queries for Neo4j versions prior 2.0
- The non transactional Cypher will be removed eventually, so we create now
  a transaction per query automatically
- Experimental support for IPython Notebook rendering
- Fix #101. Fix a problem when accessing node properties inside transaction
  for queries


2.0.1 (2014-03-23)
------------------
- Fix coveralls for Travis
- Fix #100. Fixes rollback problem when outside a with statement
- Update Neo4j versions for testing
- Remove inrange test for version 1.7.2 of Neo4j
- Add specific test for inrange lookups
- Fixes #98. Bug due to an incorrect treatment of numbers in eq, equals,
  neq, notequals lookups
- Add downloads
- Split exceptions from request.py file to a exceptions.py file
- Update requirements.txt
- Fix #96, fix dependency versions
- Fix #95. Support for creating spatial indexes


2.0.0 (2013-12-30)
------------------
- Add support for Neo4j 2.0
- Add Python3 support
- Remove Python 2.6 support
- Add support for Cypher transactional endpoint
- Add documentation for Cypher transactions
- Add support for Labels
- Add documentation for Labels
- Add support to pass Neo4j URL as the host, and neo4j-rest-client will request
  for the '/db/data' part in an extra request
- Add option for enabling verification of SSL certificates
- Fix #94. Disable lazy loading from Cypher queries but keep if for filters
- Update documentation
- Add the option to 'create' labels and add nodes to them
- Add filtering support for Labels
- Add tests for Labels
- Better structure to organize tests
- Add UnitTest.skipIf instead of my own decorator @versions
- Add development requirements and PyPy to Travis
- Add flake8
- Add support for tox
- Skip some test that depend on newer versions of other dependencies
- Update README with Coveralls.io image
- Add coverage
- Add extra requires for tests
- Enable syntax highlighting, fix spelling errors
- Fix #92. Allow nodes to be deleted from index without key or value
- Fix an error on traversals time_out when decimal values are passed
- Update Neo4j versions for Travis
- PEP8 review
- Add .all method to get all the elements. Underneath, it invokes .filter
  with no arguments
- Merge pull request #85 from carlsonp/patch-1


1.9.0 (2013-05-27)
------------------
- Add Neo4j 1.9 and 2.0.0-M02 to tests and Travis.
- Fix Python 2.6 compatibility. Last Python 2.6 issue fixed.
- Fix test_filter_nodes_complex_lookups test for empty databases
- Fix get_or_create and create_or_fail tests and add SMART_ERRORS for those functions
- Add support for Neo4j versions when testing in Travis
- Add support for get_or_create and create_or_fail index operations
- Adding integration tests with Travis-CI
- Updated requirements.txt with Shrubbery proposals
- Add experimental support for smart dates


1.8.0 (2012-12-09)
------------------
- Updated lucene-querybuilder requirement.
- Add support for using Indexes as start points when filtering
- Add support for using filters in indices.
- Fixes an error when using cert and key files.
- Adding order by and filtering for relationships.
- First implementation of complex filtering and slicing for nodes based on
  Cypher.
- Improving stability of tests.
- Fixes #74. Added the new .query() method and casting for returns. Also a very
  initial .filter method with an special Q object for composing complex filters.
- Fixes #64, added a small unicode check.
- Feature cache store and cache extension requests. Every time extension is used
  a get request is made before post this only needs to happen once per extension.
- Allow user to configure own cache engine, (e.g djangos cache).
- Read test db url from environ.
- Fixes #71. Pass correct url to get. Get with missing '/' was causing an
  additional 302.
- Support keep-alive / pipelining: httplib now instantiated on module load not
  per quest this also fixes caching, when the CACHE option was set a no-cache
  header was added that by passed the cache system.
- Fixes #68. Gremlin query trips on "simple" list, but not an error no
  neo4j-rest-client side.
- Fixes #69. Incorrect node references when splitting transactions.
- Adding support for retrieving index elements in a transaction.
- Fixes #66. Ditch exception catch on root fetch at GraphDatabase.__init__().
  As per #65, current behaviour when auth fails is that a 401 StatusException
  is raised, and caught by this try/except block and a misleading NotFoundError
  is raised in its place - lets just let the StatusException through. Unsure
  about what other Exceptions may be raised but cannot reproduce.
- Fixed issue #69. Transaction split.
- Adding support for retrieving index elements in a transaction.


1.7.0 (2012-05-17)
------------------
- Fixing an error when reating relationships with nodes created previously in
  a transactions.
- Fixing typo (self._aith vs self_auth).
- Fixing #60. Adding support when no port is specified.
- Fixing an error with unicode property names and indexing.


1.6.2 (2012-03-26)
------------------
- Fixing an error indexing with numeric values.
- Fixing an error indexing with boolean values.
- Adding initial unicode suppport for indices.
  Adding better debug messages to 400 response codes.


1.6.1 (2012-02-27)
------------------
- Fixes #29. Adding support for authentication.


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
- Updated to using lucene-querybuilder 0.1.5 (bugfixes and better wildcard
  support).
- Fixed the test issue found in #34, and updated the REST client to using
  lucene-querybuilder 0.1.5.
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
