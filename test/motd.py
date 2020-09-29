import unittest
import ircstates, irctokens

class MOTDTest(unittest.TestCase):
    def test(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise("375 * :start of motd"))
        server.parse_tokens(irctokens.tokenise("372 * :first line of motd"))
        server.parse_tokens(irctokens.tokenise("372 * :second line of motd"))
        self.assertEqual(server.motd, [
            "start of motd",
            "first line of motd",
            "second line of motd"])
