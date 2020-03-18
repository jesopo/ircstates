import unittest
import ircstates, irctokens

class EmitTest(unittest.TestCase):
    def test_join(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        emits = server.parse_tokens(
            irctokens.tokenise(":nickname JOIN #chan"))[0]

        self.assertIn(ircstates.EmitCommand("JOIN"), emits)
        self.assertIn(ircstates.EmitSourceSelf(), emits)
        user = server.users["nickname"]
        self.assertIn(ircstates.EmitSourceUser(user), emits)
        channel = server.channels["#chan"]
        self.assertIn(ircstates.EmitChannel(channel), emits)

        emits = server.parse_tokens(
            irctokens.tokenise(":other JOIN #chan"))[0]
        self.assertNotIn(ircstates.EmitSourceSelf(), emits)
        other = server.users["other"]
        self.assertIn(ircstates.EmitSourceUser(other), emits)

    def test_privmsg(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        emits = server.parse_tokens(
            irctokens.tokenise(":nickname PRIVMSG #chan :hello"))[0]

        self.assertIn(ircstates.EmitCommand("PRIVMSG"), emits)
        self.assertIn(ircstates.EmitText("hello"), emits)
        self.assertIn(ircstates.EmitSourceSelf(), emits)
        user = server.users["nickname"]
        self.assertIn(ircstates.EmitSourceUser(user), emits)
        channel = server.channels["#chan"]
        self.assertIn(ircstates.EmitChannel(channel), emits)

        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        emits = server.parse_tokens(
            irctokens.tokenise(":other PRIVMSG #chan :hello"))[0]
        self.assertNotIn(ircstates.EmitSourceSelf(), emits)
        other = server.users["other"]
        self.assertIn(ircstates.EmitSourceUser(other), emits)

    def test_privmsg_nojoin(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))

        emits = server.parse_tokens(
            irctokens.tokenise(":other PRIVMSG #chan :hello"))[0]

        self.assertIn(ircstates.EmitCommand("PRIVMSG"), emits)
        self.assertIn(ircstates.EmitText("hello"), emits)
        self.assertNotIn(ircstates.EmitSourceSelf(), emits)
        self.assertIn(ircstates.EmitSourceUser(
            server.create_user("other", "other")), emits)
        channel = server.channels["#chan"]
        self.assertIn(ircstates.EmitChannel(channel), emits)
