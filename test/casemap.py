import unittest
from ircstates.casemap import casefold

class CaseMapTest(unittest.TestCase):
    def test_rfc1459(self):
        lower = casefold("rfc1459", "ÀTEST[]~\\")
        self.assertEqual(lower, "Àtest{}^|")

    def test_ascii(self):
        lower = casefold("ascii", "ÀTEST[]~\\")
        self.assertEqual(lower, "Àtest[]~\\")
