import unittest
import ircstates, irctokens

class ChannelTest(unittest.TestCase):
    def test_self_join(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        self.assertIn("#chan", server.channels)
        self.assertEqual(len(server.channels), 1)
