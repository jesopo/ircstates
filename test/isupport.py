import unittest
import ircstates, irctokens

class ISUPPORTTest(unittest.TestCase):
    def test_chanmodes(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        self.assertEqual(server.isupport.chanmodes.a_modes, ["b"])
        self.assertEqual(server.isupport.chanmodes.b_modes, ["k"])
        self.assertEqual(server.isupport.chanmodes.c_modes, ["l"])
        self.assertEqual(server.isupport.chanmodes.d_modes,
            ["i", "m", "n", "p", "s", "t"])
        server.parse_tokens(irctokens.tokenise("005 * CHANMODES=a,b,c,d *"))
        self.assertEqual(server.isupport.chanmodes.a_modes, ["a"])
        self.assertEqual(server.isupport.chanmodes.b_modes, ["b"])
        self.assertEqual(server.isupport.chanmodes.c_modes, ["c"])
        self.assertEqual(server.isupport.chanmodes.d_modes, ["d"])

    def test_prefix(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
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
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        self.assertEqual(server.isupport.chantypes, ["#"])
        server.parse_tokens(irctokens.tokenise("005 * CHANTYPES=#& *"))
        self.assertEqual(server.isupport.chantypes, ["#", "&"])

    def test_modes(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        self.assertEqual(server.isupport.modes, 3)
        server.parse_tokens(irctokens.tokenise("005 * MODES *"))
        self.assertEqual(server.isupport.modes, -1)
        server.parse_tokens(irctokens.tokenise("005 * MODES=5 *"))
        self.assertEqual(server.isupport.modes, 5)

    def test_rfc1459(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        self.assertEqual(server.isupport.casemapping, "rfc1459")
        server.parse_tokens(irctokens.tokenise("005 * CASEMAPPING=rfc1459 *"))
        self.assertEqual(server.isupport.casemapping, "rfc1459")

    def test_ascii(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise("005 * CASEMAPPING=ascii *"))
        self.assertEqual(server.isupport.casemapping, "ascii")

    def test_fallback_to_rfc1459(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise("005 * CASEMAPPING=asd *"))
        self.assertEqual(server.isupport.casemapping, "rfc1459")

    def test_network(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        self.assertIsNone(server.isupport.network)
        server.parse_tokens(irctokens.tokenise("005 * NETWORK=testnet *"))
        self.assertEqual(server.isupport.network, "testnet")

    def test_statusmsg(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        self.assertEqual(server.isupport.statusmsg, [])
        server.parse_tokens(irctokens.tokenise("005 * STATUSMSG=&@ *"))
        self.assertEqual(server.isupport.statusmsg, ["&", "@"])

    def test_callerid(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        self.assertIsNone(server.isupport.callerid)
        server.parse_tokens(irctokens.tokenise("005 * CALLERID=U *"))
        self.assertEqual(server.isupport.callerid, "U")
        server.parse_tokens(irctokens.tokenise("005 * CALLERID *"))
        self.assertEqual(server.isupport.callerid, "g")

    def test_excepts(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        self.assertIsNone(server.isupport.excepts)
        server.parse_tokens(irctokens.tokenise("005 * EXCEPTS=U *"))
        self.assertEqual(server.isupport.excepts, "U")
        server.parse_tokens(irctokens.tokenise("005 * EXCEPTS *"))
        self.assertEqual(server.isupport.excepts, "e")

    def test_invex(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        self.assertIsNone(server.isupport.invex)
        server.parse_tokens(irctokens.tokenise("005 * INVEX=U *"))
        self.assertEqual(server.isupport.invex, "U")
        server.parse_tokens(irctokens.tokenise("005 * INVEX *"))
        self.assertEqual(server.isupport.invex, "I")

    def test_whox(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        self.assertFalse(server.isupport.whox)
        server.parse_tokens(irctokens.tokenise("005 * WHOX *"))
        self.assertTrue(server.isupport.whox)

    def test_monitor(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        self.assertIsNone(server.isupport.monitor)
        server.parse_tokens(irctokens.tokenise("005 * MONITOR=123 *"))
        self.assertEqual(server.isupport.monitor, 123)
        server.parse_tokens(irctokens.tokenise("005 * MONITOR *"))
        self.assertEqual(server.isupport.monitor, -1)

    def test_watch(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        self.assertIsNone(server.isupport.watch)
        server.parse_tokens(irctokens.tokenise("005 * WATCH=123 *"))
        self.assertEqual(server.isupport.watch, 123)
        server.parse_tokens(irctokens.tokenise("005 * WATCH *"))
        self.assertEqual(server.isupport.watch, -1)
