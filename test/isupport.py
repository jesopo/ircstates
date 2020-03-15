import unittest
import ircstates, irctokens

class ISUPPORTTest(unittest.TestCase):
    def test_chanmodes(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        self.assertEqual(server.isupport.chanmodes.list_modes,      ["b"])
        self.assertEqual(server.isupport.chanmodes.setting_b_modes, ["k"])
        self.assertEqual(server.isupport.chanmodes.setting_c_modes, ["l"])
        self.assertEqual(server.isupport.chanmodes.setting_d_modes,
            ["i", "m", "n", "p", "s", "t"])
        server.parse_tokens(irctokens.tokenise("005 * CHANMODES=a,b,c,d *"))
        self.assertEqual(server.isupport.chanmodes.list_modes,      ["a"])
        self.assertEqual(server.isupport.chanmodes.setting_b_modes, ["b"])
        self.assertEqual(server.isupport.chanmodes.setting_c_modes, ["c"])
        self.assertEqual(server.isupport.chanmodes.setting_d_modes, ["d"])

    def test_prefix(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        self.assertEqual(server.isupport.prefix.modes, ["o", "v"])
        self.assertEqual(server.isupport.prefix.prefixes, ["@", "+"])

        self.assertEqual(server.isupport.prefix.from_mode("o"), "@")
        self.assertIsNone(server.isupport.prefix.from_mode("a"))
        self.assertEqual(server.isupport.prefix.from_prefix("@"), "o")
        self.assertIsNone(server.isupport.prefix.from_prefix("&"))

        server.parse_tokens(irctokens.tokenise("005 * PREFIX=(qaohv)~&@%+ *"))
        self.assertEqual(server.isupport.prefix.modes,
            ["q", "a", "o", "h", "v"])
        self.assertEqual(server.isupport.prefix.prefixes,
            ["~", "&", "@", "%", "+"])
        self.assertEqual(server.isupport.prefix.from_mode("a"), "&")
        self.assertEqual(server.isupport.prefix.from_prefix("&"), "a")


    def test_chantypes(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        self.assertEqual(server.isupport.chantypes, ["#"])
        server.parse_tokens(irctokens.tokenise("005 * CHANTYPES=#& *"))
        self.assertEqual(server.isupport.chantypes, ["#", "&"])

    def test_modes(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        self.assertEqual(server.isupport.modes, 3)
        server.parse_tokens(irctokens.tokenise("005 * MODES *"))
        self.assertEqual(server.isupport.modes, -1)
        server.parse_tokens(irctokens.tokenise("005 * MODES=5 *"))
        self.assertEqual(server.isupport.modes, 5)

    def test_rfc1459(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        self.assertEqual(server.isupport.casemapping, "rfc1459")
        lower = server.casemap_lower("ÀTEST[]~\\")
        self.assertEqual(lower, "Àtest{}^|")

    def test_ascii(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise("005 * CASEMAPPING=ascii *"))
        self.assertEqual(server.isupport.casemapping, "ascii")
        lower = server.casemap_lower("ÀTEST[]~\\")
        self.assertEqual(lower, "Àtest[]~\\")

    def test_fallback_to_rfc1459(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise("005 * CASEMAPPING=asd *"))
        self.assertEqual(server.isupport.casemapping, "rfc1459")
        lower = server.casemap_lower("ÀTEST[]~\\")
        self.assertEqual(lower, "Àtest{}^|")
