# -*- coding: utf-8 -*-
import unittest

from neo4jrestclient.exceptions import (
    StatusException, NotFoundError, TransactionException
)


class ExceptionsTestCase(unittest.TestCase):

    def test_status_exception_params(self):
        StatusException(402, "Message")

    def test_not_found_error(self):
        NotFoundError()

    def test_not_found_error_params(self):
        NotFoundError("Message")

    def test_transaction_exception(self):
        TransactionException()

    def test_transaction_params(self):
        TransactionException(200, "Message")
