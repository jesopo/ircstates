import unittest
import ircstates, irctokens

class NicknameTestChange(unittest.TestCase):
    def test_self_change(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname NICK nickname2"))
        self.assertEqual(server.nickname, "nickname2")

    def test_other_change(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        self.assertIn("other", server.users)

        server.parse_tokens(irctokens.tokenise(":other NICK other2"))
        self.assertNotIn("other", server.users)
        self.assertIn("other2", server.users)
