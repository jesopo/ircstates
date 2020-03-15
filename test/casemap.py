import unittest
import ircstates, irctokens

class CaseMapTestMethod(unittest.TestCase):
    def test_rfc1459(self):
        lower = ircstates.casefold("rfc1459", "ÀTEST[]~\\")
        self.assertEqual(lower, "Àtest{}^|")

    def test_ascii(self):
        lower = ircstates.casefold("ascii", "ÀTEST[]~\\")
        self.assertEqual(lower, "Àtest[]~\\")

class CaseMapTestCommands(unittest.TestCase):
    def test_join(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":Nickname JOIN #Chan"))
        server.parse_tokens(irctokens.tokenise(":Other JOIN #Chan"))
        self.assertIn("nickname", server.users)
        self.assertNotIn("Nickname", server.users)
        self.assertIn("other", server.users)
        self.assertNotIn("Other", server.users)
        self.assertIn("#chan", server.channels)
        channel = server.channels["#chan"]
        self.assertEqual(channel.name, "#Chan")
        user1 = server.users["nickname"]
        user2 = server.users["other"]
        self.assertIn(user1, server.channel_users[channel])
        self.assertIn(user2, server.channel_users[channel])
        self.assertEqual(len(server.channel_users[channel]), 2)

    def test_nick(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        user = server.users["nickname"]
        server.parse_tokens(irctokens.tokenise(":nickname NICK NewNickname"))
        self.assertEqual(len(server.users), 1)
        self.assertIn("newnickname", server.users)
        self.assertEqual(user.nickname, "NewNickname")
        self.assertEqual(user.nickname_lower, "newnickname")
        self.assertEqual(server.nickname, "NewNickname")
        self.assertEqual(server.nickname_lower, "newnickname")
