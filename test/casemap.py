import unittest
import ircstates, irctokens

class CaseMapTest(unittest.TestCase):
    def test_rfc1459(self):
        lower = ircstates.casefold("rfc1459", "ÀTEST[]~\\")
        self.assertEqual(lower, "Àtest{}^|")

    def test_ascii(self):
        lower = ircstates.casefold("ascii", "ÀTEST[]~\\")
        self.assertEqual(lower, "Àtest[]~\\")

    def test_join(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 Nickname"))
        server.parse_tokens(irctokens.tokenise(":Nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":Other JOIN #chan"))
        self.assertIn("other", server.users)
