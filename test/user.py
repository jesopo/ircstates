import unittest
import ircstates, irctokens

class UserTestNicknameChange(unittest.TestCase):
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

class UserTestUserHostSelf(unittest.TestCase):
    def test_both(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(
            irctokens.tokenise(":nickname!user@host JOIN #chan"))
        self.assertEqual(server.username, "user")
        self.assertEqual(server.hostname, "host")

    def test_user(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname!user JOIN #chan"))
        self.assertEqual(server.username, "user")
        self.assertIsNone(server.hostname)

    def test_host(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname@host JOIN #chan"))
        self.assertIsNone(server.username)
        self.assertEqual(server.hostname, "host")

class UserTestUserHostOther(unittest.TestCase):
    def test_both(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other!user@host JOIN #chan"))
        user = server.users["other"]
        self.assertEqual(user.username, "user")
        self.assertEqual(user.hostname, "host")

    def test_user(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other!user JOIN #chan"))
        user = server.users["other"]
        self.assertEqual(user.username, "user")
        self.assertIsNone(user.hostname)

    def test_host(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other@host JOIN #chan"))
        user = server.users["other"]
        self.assertIsNone(user.username)
        self.assertEqual(user.hostname, "host")

class UserTestPRIVMSGSelfHostmask(unittest.TestCase):
    def test_both(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise(":nickname!user@host PRIVMSG #chan :hi"))
        self.assertEqual(server.username, "user")
        self.assertEqual(server.hostname, "host")

    def test_user(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise(":nickname!user PRIVMSG #chan :hi"))
        self.assertEqual(server.username, "user")
        self.assertIsNone(server.hostname)

    def test_host(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise(":nickname@host PRIVMSG #chan :hi"))
        self.assertIsNone(server.username)
        self.assertEqual(server.hostname, "host")

class UserTestPRIVMSGOtherHostmask(unittest.TestCase):
    def test_both(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise(":other!user@host PRIVMSG #chan :hi"))
        user = server.users["other"]
        self.assertEqual(user.username, "user")
        self.assertEqual(user.hostname, "host")

    def test_user(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise(":other!user PRIVMSG #chan :hi"))
        user = server.users["other"]
        self.assertEqual(user.username, "user")
        self.assertIsNone(user.hostname)

    def test_host(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise(":other@host PRIVMSG #chan :hi"))
        user = server.users["other"]
        self.assertIsNone(user.username)
        self.assertEqual(user.hostname, "host")

class UserTestVisibleHost(unittest.TestCase):
    def test_without_username(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise("396 * hostname"))
        self.assertIsNone(server.username)
        self.assertEqual(server.hostname, "hostname")

    def test_with_username(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise("396 * username@hostname"))
        self.assertEqual(server.username, "username")
        self.assertEqual(server.hostname, "hostname")

class UserTestWHO(unittest.TestCase):
    def test_realname(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
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

