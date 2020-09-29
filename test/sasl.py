import unittest
import ircstates, irctokens

class SASLTestAccount(unittest.TestCase):
    def test_loggedin(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("900 * nick!user@host account *"))

        self.assertEqual(server.nickname, "nick")
        self.assertEqual(server.username, "user")
        self.assertEqual(server.hostname, "host")
        self.assertEqual(server.account,  "account")

    def test_loggedout(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("900 * nick!user@host account *"))
        server.parse_tokens(irctokens.tokenise("901 * nick1!user1@host1 *"))

        self.assertEqual(server.nickname, "nick1")
        self.assertEqual(server.username, "user1")
        self.assertEqual(server.hostname, "host1")
        self.assertEqual(server.account,  None)
