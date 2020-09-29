import unittest
import ircstates, irctokens
from ircstates.server import WHO_TYPE

class WHOTest(unittest.TestCase):
    def test_who(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        user = server.users["nickname"]
        server.parse_tokens(irctokens.tokenise(
            "352 * #chan user host server nickname * :0 real"))

        self.assertEqual(user.username, "user")
        self.assertEqual(user.hostname, "host")
        self.assertEqual(user.realname, "real")
        self.assertEqual(user.server,   "server")
        self.assertIsNone(user.away)

        self.assertEqual(server.username, user.username)
        self.assertEqual(server.hostname, user.hostname)
        self.assertEqual(server.realname, user.realname)
        self.assertEqual(server.server,   user.server)
        self.assertIsNone(server.away)

        server.parse_tokens(irctokens.tokenise(
            "352 * #chan user host server nickname G* :0 real"))
        self.assertEqual(user.away,   "")
        self.assertEqual(server.away, "")

    def test_whox(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        user = server.users["nickname"]
        server.parse_tokens(irctokens.tokenise(
            f"354 * {WHO_TYPE} user 1.2.3.4 host server nickname * account :real"))

        self.assertEqual(user.username, "user")
        self.assertEqual(user.hostname, "host")
        self.assertEqual(user.realname, "real")
        self.assertEqual(user.account,  "account")
        self.assertEqual(user.server,   "server")
        self.assertIsNone(user.away)
        self.assertEqual(user.ip,       "1.2.3.4")

        self.assertEqual(server.username, user.username)
        self.assertEqual(server.hostname, user.hostname)
        self.assertEqual(server.realname, user.realname)
        self.assertEqual(server.account,  user.account)
        self.assertEqual(server.server,   user.server)
        self.assertIsNone(server.away)
        self.assertEqual(server.ip,       user.ip)

        server.parse_tokens(irctokens.tokenise(
            f"354 * {WHO_TYPE} user realip host server nickname G account :real"))
        self.assertEqual(user.away,   "")
        self.assertEqual(server.away, "")

    def test_whox_no_account(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))

        user = server.users["nickname"]
        user.account   = "account"
        server.account = "account"

        server.parse_tokens(irctokens.tokenise(
            f"354 * {WHO_TYPE} user realip host server nickname * 0 :real"))

        self.assertEqual(user.account,   None)
        self.assertEqual(server.account, user.account)

    def test_whox_ipv6(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))

        user = server.users["nickname"]

        server.parse_tokens(irctokens.tokenise(
            f"354 * {WHO_TYPE} user 0::1 host server nickname * 0 :real"))
        self.assertEqual(user.ip, "::1")

        server.parse_tokens(irctokens.tokenise(
            f"354 * {WHO_TYPE} user 00::2 host server nickname * 0 :real"))
        self.assertEqual(user.ip, "::2")

        server.parse_tokens(irctokens.tokenise(
            f"354 * {WHO_TYPE} user fd00:0:0:0::1 host server nickname * 0 :real"))
        self.assertEqual(user.ip, "fd00::1")
