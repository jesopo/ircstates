import unittest
import ircstates, irctokens
from ircstates.server import WHO_TYPE

class WHOTest(unittest.TestCase):
    def test_who(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(
            "352 * #chan user host server nickname * :0 real"))
        user = server.users["nickname"]

        self.assertEqual(user.username, "user")
        self.assertEqual(user.hostname, "host")
        self.assertEqual(user.realname, "real")

        self.assertEqual(server.username, user.username)
        self.assertEqual(server.hostname, user.hostname)
        self.assertEqual(server.realname, user.realname)

    def test_whox(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(
            f"354 * {WHO_TYPE} user realip host nickname account :real"))
        user = server.users["nickname"]

        self.assertEqual(user.username, "user")
        self.assertEqual(user.hostname, "host")
        self.assertEqual(user.realname, "real")
        self.assertEqual(user.account,  "account")

        self.assertEqual(server.username, user.username)
        self.assertEqual(server.hostname, user.hostname)
        self.assertEqual(server.realname, user.realname)
        self.assertEqual(server.account,  user.account)

    def test_whox_no_account(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(
            f"354 * {WHO_TYPE} user realip host nickname 0 :real"))
        user = server.users["nickname"]

        self.assertEqual(user.account,   None)
        self.assertEqual(server.account, user.account)
