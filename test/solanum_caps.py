from ircstates.server import Server
import unittest

import ircstates, irctokens


class SolanumCapTests(unittest.TestCase):
    def _create_server(self) -> ircstates.Server:
        server = Server('test')
        server.nickname = 'theserver'
        server.nickname_lower = 'theserver'
        server.parse_tokens(irctokens.tokenise(':theserver!who@cares JOIN #test'))
        server._add_user('some', 'some')
        return server

    def test_setoper(self):
        server = self._create_server()
        server.agreed_caps.append('solanum.chat/oper')
        server.parse_tokens(irctokens.tokenise('@solanum.chat/oper=derg :some!one@host JOIN #test'))
        user = server.users['some']
        self.assertTrue(user.is_oper)
        self.assertEqual(user.oper_name, 'derg')

    def test_sethost(self):
        server = self._create_server()
        server.agreed_caps.append('solanum.chat/realhost')
        server.parse_tokens(
            irctokens.tokenise('@solanum.chat/realhost=someones_got_a_host :some!one@other_host JOIN #test')
        )
        user = server.users['some']

        self.assertEqual(user.hostname, 'other_host')
        self.assertEqual(user.real_host, 'someones_got_a_host')

    def test_setip(self):
        server = self._create_server()
        server.agreed_caps.append('solanum.chat/realhost')
        server.parse_tokens(
            irctokens.tokenise('@solanum.chat/ip=1.2.3.4 :some!one@other_host JOIN #test')
        )
        user = server.users['some']

        self.assertEqual(user.hostname, 'other_host')
        self.assertEqual(user.real_ip, '1.2.3.4')
