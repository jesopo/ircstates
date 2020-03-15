import unittest
from datetime import datetime
import ircstates, irctokens

class ChannelTestJoin(unittest.TestCase):
    def test_self_join(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        self.assertIn("#chan", server.channels)
        self.assertIn("nickname", server.users)
        self.assertEqual(len(server.users), 1)
        self.assertEqual(len(server.channels), 1)

        self.assertIn(server.channels["#chan"], server.channel_users)
        self.assertIn(server.users["nickname"], server.user_channels)
        self.assertEqual(len(server.user_channels), 1)
        self.assertEqual(len(server.channel_users), 1)

    def test_other_join(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        self.assertEqual(len(server.users), 2)
        self.assertIn("other", server.users)
        self.assertEqual(len(server.user_channels), 2)
        self.assertEqual(len(server.channel_users), 1)

class ChannelTestPart(unittest.TestCase):
    def test_self_part(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":nickname PART #chan"))
        self.assertEqual(len(server.users), 0)
        self.assertEqual(len(server.channels), 0)
        self.assertEqual(len(server.user_channels), 0)
        self.assertEqual(len(server.channel_users), 0)

    def test_other_part(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other PART #chan"))

        user = server.users["nickname"]
        channel = server.channels["#chan"]

        self.assertEqual(len(server.users), 1)
        self.assertEqual(len(server.channels), 1)
        self.assertIn(user, server.user_channels)
        self.assertEqual(len(server.user_channels[user]), 1)
        self.assertIn(channel, server.channel_users)
        self.assertEqual(len(server.channel_users), 1)
        self.assertIn(user, server.channel_users[channel])
        self.assertEqual(len(server.user_channels), 1)

class ChannelTestKick(unittest.TestCase):
    def test_self_kick(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("KICK #chan nickname"))
        self.assertEqual(len(server.users), 0)
        self.assertEqual(len(server.channels), 0)
        self.assertEqual(len(server.user_channels), 0)
        self.assertEqual(len(server.channel_users), 0)

    def test_other_kick(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("KICK #chan other"))

        user = server.users["nickname"]
        channel = server.channels["#chan"]

        self.assertEqual(len(server.users), 1)
        self.assertEqual(len(server.channels), 1)
        self.assertIn(user, server.user_channels)
        self.assertEqual(len(server.user_channels[user]), 1)
        self.assertIn(channel, server.channel_users)
        self.assertEqual(len(server.channel_users), 1)
        self.assertIn(user, server.channel_users[channel])
        self.assertEqual(len(server.user_channels), 1)

class ChannelTestTopic(unittest.TestCase):
    def test_text(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("332 * #chan :test"))
        self.assertEqual(server.channels["#chan"].topic, "test")

    def test_set_by_at(self):
        dt = datetime(2020, 3, 12, 14, 27, 57)
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("333 * #chan other 1584023277"))
        channel = server.channels["#chan"]
        self.assertEqual(channel.topic_setter, "other")
        self.assertEqual(channel.topic_time, dt)

    def test_topic_command(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("TOPIC #chan :hello there"))
        self.assertEqual(server.channels["#chan"].topic, "hello there")

class ChannelTestCreation(unittest.TestCase):
    def test(self):
        dt = datetime(2020, 3, 12, 19, 38, 9)
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("329 * #chan 1584041889"))
        self.assertEqual(server.channels["#chan"].created, dt)

class ChannelTestNAMES(unittest.TestCase):
    def test(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("353 * * #chan :nickname @+other"))
        self.assertIn("nickname", server.users)
        self.assertIn("other", server.users)
        user = server.users["other"]
        self.assertIn(user, server.user_channels)
        channel = server.channels["#chan"]
        self.assertIn(user, server.channel_users[channel])
        channel_user = server.channel_users[channel][user]
        self.assertEqual(channel_user.modes, ["o", "v"])

    def test_userhost_in_names(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(
            "353 * * #chan :nickname!user@host other!user2@host2"))
        self.assertEqual(server.username, "user")
        self.assertEqual(server.hostname, "host")
        user = server.users["other"]
        self.assertEqual(user.username, "user2")
        self.assertEqual(user.hostname, "host2")
