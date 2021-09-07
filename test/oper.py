import unittest

import ircstates
import irctokens
from ircstates.numerics import RPL_YOUREOPER


class OperTests(unittest.TestCase):

    def test_oper_up(self):
        server = ircstates.Server('server')
        server.nickname = server.nickname_lower = 'server'
        server.parse_tokens(irctokens.tokenise(
            f':a.server {RPL_YOUREOPER} :we take no responsibility for the testing you\'re about to endure')
        )

        self.assertTrue(server.is_oper)

    def test_deoper(self):
        server = ircstates.Server('server')
        server.nickname = server.nickname_lower = 'server'
        server.parse_tokens(irctokens.tokenise(
            f':a.server {RPL_YOUREOPER} :we take no responsibility for the testing you\'re about to endure')
        )

        server.parse_tokens(irctokens.tokenise(':a.server MODE server -oButMOre'))

        self.assertFalse(server.is_oper)
