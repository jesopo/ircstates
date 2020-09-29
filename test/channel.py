import unittest
import pendulum
import ircstates, irctokens

class ChannelTestJoin(unittest.TestCase):
    def test_self_join(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        self.assertIn("#chan", server.channels)
        self.assertIn("nickname", server.users)
        self.assertEqual(len(server.users), 1)
        self.assertEqual(len(server.channels), 1)

        user = server.users["nickname"]
        channel = server.channels["#chan"]
        self.assertIn(user.nickname_lower, channel.users)
        channel_user = channel.users[user.nickname_lower]
        self.assertEqual(user.channels, set([channel.name_lower]))

    def test_other_join(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        self.assertEqual(len(server.users), 2)
        self.assertIn("other", server.users)
        channel = server.channels["#chan"]
        self.assertEqual(len(channel.users), 2)

        user = server.users["other"]
        self.assertEqual(user.channels, set([channel.name_lower]))

class ChannelTestPart(unittest.TestCase):
    def test_self_part(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":nickname PART #chan"))
        self.assertEqual(len(server.users), 0)
        self.assertEqual(len(server.channels), 0)

    def test_other_part(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other PART #chan"))

        user = server.users["nickname"]
        channel = server.channels["#chan"]
        channel_user = channel.users[user.nickname_lower]

        self.assertEqual(server.users, {"nickname": user})
        self.assertEqual(server.channels, {"#chan": channel})
        self.assertEqual(user.channels, set([channel.name_lower]))
        self.assertEqual(channel.users, {"nickname": channel_user})

class ChannelTestKick(unittest.TestCase):
    def test_self_kick(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(
            irctokens.tokenise(":nickname KICK #chan nickname"))
        self.assertEqual(len(server.users), 0)
        self.assertEqual(len(server.channels), 0)

    def test_other_kick(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":other JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(":nickname KICK #chan other"))

        user = server.users["nickname"]
        channel = server.channels["#chan"]
        channel_user = channel.users[user.nickname_lower]

        self.assertEqual(len(server.users), 1)
        self.assertEqual(len(server.channels), 1)
        self.assertEqual(user.channels, set([channel.name_lower]))
        self.assertEqual(channel.users, {user.nickname_lower: channel_user})

class ChannelTestTopic(unittest.TestCase):
    def test_text(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("332 * #chan :test"))
        self.assertEqual(server.channels["#chan"].topic, "test")

    def test_set_by_at(self):
        dt = pendulum.datetime(2020, 3, 12, 14, 27, 57)
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("333 * #chan other 1584023277"))
        channel = server.channels["#chan"]
        self.assertEqual(channel.topic_setter, "other")
        self.assertEqual(channel.topic_time, dt)

    def test_topic_command(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("TOPIC #chan :hello there"))
        self.assertEqual(server.channels["#chan"].topic, "hello there")

class ChannelTestCreation(unittest.TestCase):
    def test(self):
        dt = pendulum.datetime(2020, 3, 12, 19, 38, 9)
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("329 * #chan 1584041889"))
        self.assertEqual(server.channels["#chan"].created, dt)

class ChannelTestNAMES(unittest.TestCase):
    def test(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise("353 * * #chan :nickname @+other"))
        self.assertIn("nickname", server.users)
        self.assertIn("other", server.users)

        user = server.users["other"]
        channel = server.channels["#chan"]
        channel_user_1 = channel.users[user.nickname_lower]
        channel_user_2 = channel.users[server.nickname_lower]

        self.assertEqual(channel.users, {
            user.nickname_lower: channel_user_1,
            server.nickname_lower: channel_user_2})
        self.assertEqual(user.channels, set([channel.name_lower]))
        self.assertEqual(channel_user_1.modes, ["o", "v"])

    def test_userhost_in_names(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))
        server.parse_tokens(irctokens.tokenise(
            "353 * * #chan :nickname!user@host other!user2@host2"))
        self.assertEqual(server.username, "user")
        self.assertEqual(server.hostname, "host")
        user = server.users["other"]
        self.assertEqual(user.username, "user2")
        self.assertEqual(user.hostname, "host2")

class ChannelNICKAfterJoin(unittest.TestCase):
    def test(self):
        server = ircstates.Server("test")
        server.parse_tokens(irctokens.tokenise("001 nickname *"))
        server.parse_tokens(irctokens.tokenise(":nickname JOIN #chan"))

        user = server.users["nickname"]
        channel = server.channels["#chan"]
        channel_user = channel.users[user.nickname_lower]
        server.parse_tokens(irctokens.tokenise(":nickname NICK Nickname2"))

        self.assertEqual(channel.users, {user.nickname_lower: channel_user})
        self.assertEqual(channel_user.nickname,       "Nickname2")
        self.assertEqual(channel_user.nickname_lower, "nickname2")
