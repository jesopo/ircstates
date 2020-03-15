import unittest
from ircstates.casemap import casefold

class CaseMapTest(unittest.TestCase):
    def test_rfc1459(self):
        lower = casefold("rfc1459", "àTEST[]\\~")
        self.assertEqual(lower, "àtest{}|^")

    def test_ascii(self):
        lower = casefold("ascii", "àTEST[]\\~")
        self.assertEqual(lower, "àtest[]\\~")
