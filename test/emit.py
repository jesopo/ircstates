import unittest
import ircstates, irctokens

class EmitTest(unittest.TestCase):
    def test_join(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        emits = server.parse_tokens(
            irctokens.tokenise(":nickname JOIN #chan"))[0]

        self.assertEqual(emits.command, "JOIN")
        self.assertEqual(emits.self,    True)
        self.assertEqual(emits.user,    server.users["nickname"])
        self.assertEqual(emits.channel, server.channels["#chan"])

        emits = server.parse_tokens(
            irctokens.tokenise(":other JOIN #chan"))[0]
        self.assertEqual(emits.command, "JOIN")
        self.assertEqual(emits.self,    None)
        self.assertEqual(emits.user,    server.users["other"])
        self.assertEqual(emits.channel, server.channels["#chan"])

    def test_privmsg(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        emits = server.parse_tokens(
            irctokens.tokenise(":nickname PRIVMSG #chan :hello"))[0]
        self.assertEqual(emits.command,     "PRIVMSG")
        self.assertEqual(emits.text,        "hello")
        self.assertEqual(emits.self_source, True)
        self.assertEqual(emits.user,        server.users["nickname"])
        self.assertEqual(emits.channel,     server.channels["#chan"])

        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        emits = server.parse_tokens(
            irctokens.tokenise(":other PRIVMSG #chan :hello2"))[0]
        self.assertEqual(emits.command,     "PRIVMSG")
        self.assertEqual(emits.text,        "hello2")
        self.assertEqual(emits.self_source, None)
        self.assertEqual(emits.user,        server.users["other"])
        self.assertEqual(emits.channel,     server.channels["#chan"])

    def test_privmsg_nojoin(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))

        emits = server.parse_tokens(
            irctokens.tokenise(":other PRIVMSG #chan :hello"))[0]

        self.assertEqual(emits.command,     "PRIVMSG")
        self.assertEqual(emits.text,        "hello")
        self.assertEqual(emits.self_source, None)
        self.assertIsNotNone(emits.user)
        channel = server.channels["#chan"]
        self.assertEqual(emits.channel,     channel)

    def test_kick(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        user = server.users["nickname"]
        channel = server.channels["#chan"]
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        user_other = server.users["other"]
        emits = server.parse_tokens(
            irctokens.tokenise(":nickname KICK #chan other :reason"))[0]

        self.assertEqual(emits.command,     "KICK")
        self.assertEqual(emits.text,        "reason")
        self.assertEqual(emits.self_source, True)
        self.assertEqual(emits.user_source, user)
        self.assertEqual(emits.user_target, user_other)
        self.assertEqual(emits.channel,     channel)

    def test_mode(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        emit = server.parse_tokens(
            irctokens.tokenise("MODE nickname x+i-i+wi-wi"))[0]

        self.assertEqual(emit.command, "MODE")
        self.assertTrue(emit.self_target)
        self.assertEqual(emit.tokens,
            ["+x", "+i", "-i", "+w", "+i", "-w", "-i"])
