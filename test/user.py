import unittest
import ircstates, irctokens

class UserTestNicknameChange(unittest.TestCase):
    def test(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname NICK Nickname2"))
        self.assertEqual(server.nickname,       "Nickname2")
        self.assertEqual(server.nickname_lower, "nickname2")

        server.parse_tokens(irctokens.tokenise(":nickname2 JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        self.assertIn("other", server.users)
        user = server.users["other"]

        server.parse_tokens(irctokens.tokenise(":other NICK Other2"))
        self.assertNotIn("other", server.users)
        self.assertIn("other2", server.users)

        self.assertEqual(user.nickname,       "Other2")
        self.assertEqual(user.nickname_lower, "other2")

class UserTestHostmaskJoin(unittest.TestCase):
    def test_both(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(
            irctokens.tokenise(":nickname!user@host JOIN #chan"))
        self.assertEqual(server.username, "user")
        self.assertEqual(server.hostname, "host")

        server.parse_tokens(irctokens.tokenise(":other!user@host JOIN #chan"))
        user = server.users["other"]
        self.assertEqual(user.username, "user")
        self.assertEqual(user.hostname, "host")
        self.assertEqual(user.userhost(), "user@host")
        self.assertEqual(user.hostmask(), "other!user@host")

    def test_user(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname!user JOIN #chan"))
        self.assertEqual(server.username, "user")
        self.assertIsNone(server.hostname)

        server.parse_tokens(irctokens.tokenise(":other!user JOIN #chan"))
        user = server.users["other"]
        self.assertEqual(user.username, "user")
        self.assertIsNone(user.hostname)
        self.assertIsNone(user.userhost())
        self.assertEqual(user.hostmask(), "other!user")

    def test_host(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname@host JOIN #chan"))
        self.assertIsNone(server.username)
        self.assertEqual(server.hostname, "host")

        server.parse_tokens(irctokens.tokenise(":other@host JOIN #chan"))
        user = server.users["other"]
        self.assertIsNone(user.username)
        self.assertEqual(user.hostname, "host")
        self.assertIsNone(user.userhost())
        self.assertEqual(user.hostmask(), "other@host")

class UserTestExtendedJoin(unittest.TestCase):
    def test_without_extended_join(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        self.assertIsNone(server.account)
        self.assertIsNone(server.realname)
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        user = server.users["other"]
        self.assertIsNone(user.account)
        self.assertIsNone(user.realname)

    def test_with_account(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan acc :realname"))
        self.assertEqual(server.account, "acc")
        self.assertEqual(server.realname, "realname")
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan acc2 :realname2"))
        user = server.users["other"]
        self.assertEqual(user.account, "acc2")
        self.assertEqual(user.realname, "realname2")

    def test_without_account(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan * :realname"))
        self.assertEqual(server.account, "")
        self.assertEqual(server.realname, "realname")
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan * :realname2"))
        user = server.users["other"]
        self.assertEqual(user.account, "")
        self.assertEqual(user.realname, "realname2")

class UserTestAccountNotify(unittest.TestCase):
    def test_with_account(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":nickname ACCOUNT acc"))
        self.assertEqual(server.account, "acc")
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other ACCOUNT acc2"))
        user = server.users["other"]
        self.assertEqual(user.account, "acc2")

    def test_without_account(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":nickname ACCOUNT *"))
        self.assertEqual(server.account, "")
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other ACCOUNT *"))
        user = server.users["other"]
        self.assertEqual(user.account, "")

class UserTestHostmaskPRIVMSG(unittest.TestCase):
    def test_both(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise(":nickname!user@host PRIVMSG #chan :hi"))
        self.assertEqual(server.username, "user")
        self.assertEqual(server.hostname, "host")
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise(":other!user@host PRIVMSG #chan :hi"))
        user = server.users["other"]
        self.assertEqual(user.username, "user")
        self.assertEqual(user.hostname, "host")

    def test_user(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise(":nickname!user PRIVMSG #chan :hi"))
        self.assertEqual(server.username, "user")
        self.assertIsNone(server.hostname)
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise(":other!user PRIVMSG #chan :hi"))
        user = server.users["other"]
        self.assertEqual(user.username, "user")
        self.assertIsNone(user.hostname)

    def test_host(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise(":nickname@host PRIVMSG #chan :hi"))
        self.assertIsNone(server.username)
        self.assertEqual(server.hostname, "host")
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise(":other@host PRIVMSG #chan :hi"))
        user = server.users["other"]
        self.assertIsNone(user.username)
        self.assertEqual(user.hostname, "host")

class UserTestVisibleHost(unittest.TestCase):
    def test_without_username(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise("396 * hostname *"))
        self.assertIsNone(server.username)
        self.assertEqual(server.hostname, "hostname")

    def test_with_username(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise("396 * username@hostname *"))
        self.assertEqual(server.username, "username")
        self.assertEqual(server.hostname, "hostname")

class UserTestWHO(unittest.TestCase):
    def test(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise("352 * #chan user host * nickname * :0 real"))
        server.parse_tokens(
            irctokens.tokenise("352 * #chan user2 host2 * other * :0 real2"))

        self.assertEqual(server.username, "user")
        self.assertEqual(server.hostname, "host")
        self.assertEqual(server.realname, "real")
        user = server.users["other"]
        self.assertEqual(user.username, "user2")
        self.assertEqual(user.hostname, "host2")
        self.assertEqual(user.realname, "real2")

class UserTestCHGHOST(unittest.TestCase):
    def test(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(
            irctokens.tokenise(":nickname!user@host JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":nickname CHGHOST u h"))
        self.assertEqual(server.username, "u")
        self.assertEqual(server.hostname, "h")
        server.parse_tokens(
            irctokens.tokenise(":other!user2@host2 JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other CHGHOST u2 h2"))
        user = server.users["other"]
        self.assertEqual(user.username, "u2")
        self.assertEqual(user.hostname, "h2")

class UserTestWHOIS(unittest.TestCase):
    def test_user_line(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("311 * nickname u h * :r"))
        self.assertEqual(server.username, "u")
        self.assertEqual(server.hostname, "h")
        self.assertEqual(server.realname, "r")

        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("311 * other u2 h2 * :r2"))
        user = server.users["other"]
        self.assertEqual(user.username, "u2")
        self.assertEqual(user.hostname, "h2")
        self.assertEqual(user.realname, "r2")

class UserTestAway(unittest.TestCase):
    def test_verb_set(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))

        user = server.users["nickname"]
        self.assertIsNone(server.away)
        self.assertIsNone(user.away)

        server.parse_tokens(irctokens.tokenise(":nickname AWAY :ik ga weg"))
        self.assertEqual(server.away, "ik ga weg")
        self.assertEqual(user.away,   "ik ga weg")

    def test_verb_unset(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        user = server.users["nickname"]

        server.parse_tokens(irctokens.tokenise(
            ":nickname AWAY :let's blow this popsicle stand"))
        server.parse_tokens(irctokens.tokenise(":nickname AWAY"))
        self.assertIsNone(server.away)
        self.assertIsNone(user.away)

    def test_numeric(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        user = server.users["nickname"]

        self.assertIsNone(server.away)
        self.assertIsNone(user.away)

        server.parse_tokens(irctokens.tokenise(
            "301 * nickname :i saw something shiny"))
        self.assertEqual(server.away, "i saw something shiny")
        self.assertEqual(user.away,   "i saw something shiny")

class UserTestSETNAME(unittest.TestCase):
    def test(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        user = server.users["other"]
        self.assertIsNone(user.realname)
        self.assertIsNone(server.realname)
        server.parse_tokens(
            irctokens.tokenise(":nickname SETNAME :new now know how"))
        server.parse_tokens(
            irctokens.tokenise(":other SETNAME :tyrannosaurus hex"))
        self.assertEqual(server.realname, "new now know how")
        self.assertEqual(user.realname, "tyrannosaurus hex")
