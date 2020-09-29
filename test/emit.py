import unittest
import ircstates, irctokens

class EmitTest(unittest.TestCase):
    def test_join(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        emit = server.parse_tokens(
            irctokens.tokenise(":nickname JOIN #chan"))

        self.assertEqual(emit.command, "JOIN")
        self.assertEqual(emit.self,    True)
        self.assertEqual(emit.user,    server.users["nickname"])
        self.assertEqual(emit.channel, server.channels["#chan"])

        emit = server.parse_tokens(
            irctokens.tokenise(":other JOIN #chan"))
        self.assertIsNotNone(emit)
        self.assertEqual(emit.command, "JOIN")
        self.assertEqual(emit.self,    None)
        self.assertEqual(emit.user,    server.users["other"])
        self.assertEqual(emit.channel, server.channels["#chan"])

    def test_privmsg(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        emit = server.parse_tokens(
            irctokens.tokenise(":nickname PRIVMSG #chan :hello"))
        self.assertIsNotNone(emit)
        self.assertEqual(emit.command,     "PRIVMSG")
        self.assertEqual(emit.text,        "hello")
        self.assertEqual(emit.self_source, True)
        self.assertEqual(emit.user,        server.users["nickname"])
        self.assertEqual(emit.channel,     server.channels["#chan"])

        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        emit = server.parse_tokens(
            irctokens.tokenise(":other PRIVMSG #chan :hello2"))
        self.assertIsNotNone(emit)
        self.assertEqual(emit.command,     "PRIVMSG")
        self.assertEqual(emit.text,        "hello2")
        self.assertEqual(emit.self_source, None)
        self.assertEqual(emit.user,        server.users["other"])
        self.assertEqual(emit.channel,     server.channels["#chan"])

    def test_privmsg_nojoin(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))

        emit = server.parse_tokens(
            irctokens.tokenise(":other PRIVMSG #chan :hello"))

        self.assertIsNotNone(emit)
        self.assertEqual(emit.command,     "PRIVMSG")
        self.assertEqual(emit.text,        "hello")
        self.assertEqual(emit.self_source, None)
        self.assertIsNotNone(emit.user)
        channel = server.channels["#chan"]
        self.assertEqual(emit.channel,     channel)

    def test_kick(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        user = server.users["nickname"]
        channel = server.channels["#chan"]
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        user_other = server.users["other"]
        emit = server.parse_tokens(
            irctokens.tokenise(":nickname KICK #chan other :reason"))

        self.assertIsNotNone(emit)
        self.assertEqual(emit.command,     "KICK")
        self.assertEqual(emit.text,        "reason")
        self.assertEqual(emit.self_source, True)
        self.assertEqual(emit.user_source, user)
        self.assertEqual(emit.user_target, user_other)
        self.assertEqual(emit.channel,     channel)

    def test_mode_self(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        emit = server.parse_tokens(
            irctokens.tokenise("MODE nickname x+i-i+wi-wi"))

        self.assertIsNotNone(emit)
        self.assertEqual(emit.command, "MODE")
        self.assertTrue(emit.self_target)
        self.assertEqual(emit.tokens,
            ["+x", "+i", "-i", "+w", "+i", "-w", "-i"])

    def test_mode_channel(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        channel = server.channels["#chan"]
        emit = server.parse_tokens(
            irctokens.tokenise(":server MODE #chan +im-m+b-k asd!*@* key"))

        self.assertIsNotNone(emit)
        self.assertEqual(emit.command, "MODE")
        self.assertEqual(emit.channel, channel)
        self.assertEqual(emit.tokens,
            ["+i", "+m", "-m", "+b asd!*@*", "-k key"])
