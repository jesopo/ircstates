import unittest
import ircstates, irctokens


class ModeTestUMode(unittest.TestCase):
    def test_add(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise("MODE nickname +i"))
        self.assertEqual(server.modes, ["i"])

    def test_remove(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise("MODE nickname +i"))
        server.parse_tokens(irctokens.tokenise("MODE nickname -i"))
        self.assertEqual(server.modes, [])

class ModeTestChannelPrefix(unittest.TestCase):
    def test_add(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise("MODE #chan +ov nickname nickname"))
        user = server.users["nickname"]
        channel = server.channels["#chan"]
        channel_user = channel.users[user.nickname_lower]
        self.assertEqual(channel_user.modes, ["o", "v"])

    def test_remove(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise("MODE #chan +ov nickname nickname"))
        server.parse_tokens(
            irctokens.tokenise("MODE #chan -ov nickname nickname"))
        user = server.users["nickname"]
        channel = server.channels["#chan"]
        channel_user = channel.users[user.nickname_lower]
        self.assertEqual(channel_user.modes, [])

class ModeTestChannelList(unittest.TestCase):
    def test_add(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("MODE #chan +b asd!*@*"))
        channel = server.channels["#chan"]
        self.assertEqual(channel.list_modes, {"b": ["asd!*@*"]})

    def test_remove(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("MODE #chan +b asd!*@*"))
        server.parse_tokens(irctokens.tokenise("MODE #chan -b asd!*@*"))
        channel = server.channels["#chan"]
        self.assertEqual(channel.list_modes, {})

class ModeTestChannelTypeB(unittest.TestCase):
    def test_add(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("MODE #chan +k password"))
        channel = server.channels["#chan"]
        self.assertEqual(channel.modes, {"k": "password"})

    def test_remove(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("MODE #chan +k password"))
        server.parse_tokens(irctokens.tokenise("MODE #chan -k *"))
        channel = server.channels["#chan"]
        self.assertEqual(channel.list_modes, {})

class ModeTestChannelTypeC(unittest.TestCase):
    def test_add(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("MODE #chan +l 100"))
        channel = server.channels["#chan"]
        self.assertEqual(channel.modes, {"l": "100"})

    def test_remove(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("MODE #chan +l 100"))
        server.parse_tokens(irctokens.tokenise("MODE #chan -l"))
        channel = server.channels["#chan"]
        self.assertEqual(channel.list_modes, {})

class ModeTestChannelTypeD(unittest.TestCase):
    def test_add(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("MODE #chan +i"))
        channel = server.channels["#chan"]
        self.assertEqual(channel.modes, {"i": None})

    def test_remove(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("MODE #chan +i"))
        server.parse_tokens(irctokens.tokenise("MODE #chan -i"))
        channel = server.channels["#chan"]
        self.assertEqual(channel.list_modes, {})

class ModeTestChannelNumeric(unittest.TestCase):
    def test(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise("324 * #chan +bkli *!*@* pass 10"))
        channel = server.channels["#chan"]
        self.assertEqual(channel.modes, {"k": "pass", "l": "10", "i": None})
        self.assertEqual(channel.list_modes, {"b": ["*!*@*"]})

    def test_without_plus(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("324 * #chan il 10"))
        channel = server.channels["#chan"]
        self.assertEqual(channel.modes, {"i": None, "l": "10"})

class ModeTestUserNumeric(unittest.TestCase):
    def test(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise("221 * +iw"))
        self.assertEqual(server.modes, ["i", "w"])

    def test_without_plus(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise("221 * iw"))
        self.assertEqual(server.modes, ["i", "w"])
