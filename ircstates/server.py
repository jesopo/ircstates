from typing import Callable, Dict, List, Optional, Set
from datetime import datetime
from irctokens import build, Line, StatefulDecoder, StatefulEncoder

from .named import Named
from .user import User
from .channel import Channel
from .channel_user import ChannelUser
from .isupport import ISupport
from .decorators import line_handler_decorator

LINE_HANDLERS: Dict[str, List[Callable[["Server", Line], None]]] = {}
line_handler = line_handler_decorator(LINE_HANDLERS)

class ServerException(Exception):
    pass
class ServerDisconnectedException(ServerException):
    pass

class Server(Named):
    def __init__(self, name: str):
        self.name = name

        self.nickname = ""

        self._encoder = StatefulEncoder()
        self._decoder = StatefulDecoder()

        self.users:    Dict[str, User]    = {}
        self.channels: Dict[str, Channel] = {}
        self.user_channels: Dict[User, Set[Channel]]        = {}
        self.channel_users: Dict[Channel, Dict[User, ChannelUser]] = {}

        self.isupport = ISupport()

    def __repr__(self) -> str:
        return f"Server(name={self.name!r})"

    def recv(self, data: bytes) -> List[Line]:
        lines = self._decoder.push(data)
        if lines is None:
            raise ServerDisconnectedException()
        for line in lines:
            self.parse_tokens(line)
        return lines

    def send(self, line: Line):
        self._encoder.push(line)
    def pending(self) -> bytes:
        return self._encoder.pending()
    def sent(self, byte_count: int) -> List[Line]:
        return self._encoder.pop(byte_count)

    def parse_tokens(self, line: Line):
        if line.command in LINE_HANDLERS:
            for callback in LINE_HANDLERS[line.command]:
                callback(self, line)

    def casemap_lower(self, s1: str):
        return s1
    def casemap_equals(self, s1: str, s2: str):
        return True

    def has_user(self, nickname: str) -> bool:
        return self.casemap_lower(nickname) in self.users
    def get_user(self, nickname: str) -> User:
        nickname_lower = self.casemap_lower(nickname)
        if not nickname_lower in self.users:
            user = User(nickname)
            user.set_nickname(nickname, nickname_lower)
            self.users[nickname_lower] = user
        return self.users[nickname_lower]

    def is_channel(self, target: str) -> bool:
        return target[:1] in self.isupport.chantypes
    def has_channel(self, name: str) -> bool:
        return self.casemap_lower(name) in self.channels
    def get_channel(self, name: str) -> Optional[Channel]:
        return self.channels.get(self.casemap_lower(name), None)

    def user_join(self, channel: Channel, user: User) -> ChannelUser:
        channel_user = ChannelUser(channel, user)
        if not user in self.user_channels:
            self.user_channels[user] =    set([])

        self.user_channels[user].add(channel)
        self.channel_users[channel][user] = channel_user
        return channel_user

    @line_handler("PING")
    def handle_ping(self, line: Line):
        self.send(build("PONG", line.params))

    @line_handler("001")
    def handle_001(self, line: Line):
        self.nickname = line.params[0]

    @line_handler("005")
    def handle_ISUPPORT(self, line: Line):
        self.isupport.tokens(line.params[1:-1])

    @line_handler("NICK")
    def handle_NICK(self, line: Line):
        new_nickname = line.params[0]
        nickname_lower = self.casemap_lower(line.hostmask.nickname)

        if nickname_lower in self.users:
            user = self.users.pop(nickname_lower)
            new_nickname_lower = self.casemap_lower(new_nickname)
            user.set_nickname(new_nickname, new_nickname_lower)
            self.users[new_nickname_lower] = user
        if line.hostmask.nickname == self.nickname:
            self.nickname = new_nickname

    @line_handler("JOIN")
    def handle_JOIN(self, line: Line):
        channel_lower = self.casemap_lower(line.params[0])
        if self.casemap_equals(line.hostmask.nickname, self.nickname):
            if not channel_lower in self.channels:
                channel = Channel(line.params[0])
                self.channels[channel_lower] = channel
                self.channel_users[channel] = {}

        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            user = self.get_user(line.hostmask.nickname)
            self.user_join(channel, user)

    @line_handler("PART")
    def handle_PART(self, line: Line):
        channel_lower = self.casemap_lower(line.params[0])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            if self.casemap_equals(line.hostmask.nickname, self.nickname):
                del self.channels[channel_lower]
                channel_users = self.channel_users.pop(channel)

                for user, cuser in channel_users.items():
                    self.user_channels[user].remove(channel)
                    if not self.user_channels[user]:
                        del self.user_channels[user]
                        del self.users[self.casemap_lower(user.nickname)]
            else:
                nickname_lower = self.casemap_lower(line.hostmask.nickname)
                if nickname_lower in self.users:
                    user = self.users[nickname_lower]
                    self.user_channels[user].remove(channel)
                    if not self.user_channels[user]:
                        del self.users[nickname_lower]
                        del self.user_channels[user]
                    del self.channel_users[channel][user]

    def _self_quit(self):
        self.users.clear()
        self.channels.clear()
        self.user_channels.clear()
        self.channel_users.clear()
        self._encoder.clear()

    @line_handler("QUIT")
    def handle_quit(self, line: Line):
        if line.hostmask.nickname == self.nickname:
            self._self_quit()
        else:
            nickname_lower = self.casemap_lower(line.hostmask.nickname)
            if nickname_lower in self.users:
                user = self.users.pop(nickname_lower)
                for channel in self.user_channels[user]:
                    del self.channel_users[channel][user]
                del self.user_channels[user]

    @line_handler("ERROR")
    def handle_ERROR(self, line: Line):
        self._self_quit()

    @line_handler("353") # user list, "NAMES #channel" response (and on-join)
    def handle_353(self, line: Line):
        channel_lower = self.casemap_lower(line.params[2])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            nicknames = list(filter(bool, line.params[3].split(" ")))
            for nickname in nicknames:
                modes = ""
                for char in nickname:
                    mode = self.isupport.prefix.from_prefix(char)
                    if mode:
                        modes += mode
                    else:
                        break
                nickname = nickname.replace(modes, "", 1)

                user = self.get_user(nickname)
                channel_user = self.user_join(channel, user)
                for mode in modes:
                    channel_user.modes.add(mode)

    @line_handler("332") # topic text, "TOPIC #channel" response (and on-join)
    def handle_332(self, line: Line):
        channel_lower = self.casemap_lower(line.params[1])
        if channel_lower in self.channels:
            self.channels[channel_lower].topic = line.params[2]
    @line_handler("333") # topic setby, "TOPIC #channel" response (and on-join)
    def handle_333(self, line: Line):
        channel_lower = self.casemap_lower(line.params[1])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            channel.topic_setter = line.params[2]
            channel.topic_time   = datetime.fromtimestamp(int(line.params[3]))
