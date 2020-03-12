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

