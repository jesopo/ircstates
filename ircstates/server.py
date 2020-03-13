from typing import Callable, Dict, List, Optional, Set, Tuple
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

        self.nickname                = ""
        self.username: Optional[str] = None
        self.hostname: Optional[str] = None
        self.realname: Optional[str] = None
        self.modes: List[str] = []
        self.motd: List[str]  = []

        self._encoder = StatefulEncoder()
        self._decoder = StatefulDecoder()

        self.users:    Dict[str, User]    = {}
        self.channels: Dict[str, Channel] = {}
        self.user_channels: Dict[User, Set[Channel]]        = {}
        self.channel_users: Dict[Channel, Dict[User, ChannelUser]] = {}

        self.isupport = ISupport()

        self._temp_caps: Dict[str, Optional[str]]     = {}
        self.caps: Optional[Dict[str, Optional[str]]] = None
        self.agreed_caps: List[str]                   = []

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
        return s1.lower()
    def casemap_equals(self, s1: str, s2: str):
        return self.casemap_lower(s1) == self.casemap_lower(s2)

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
    # first message reliably sent to us after registration is complete
    def handle_001(self, line: Line):
        self.nickname = line.params[0]

    @line_handler("005")
    # https://defs.ircdocs.horse/defs/isupport.html
    def handle_ISUPPORT(self, line: Line):
        self.isupport.tokens(line.params[1:-1])

    @line_handler("375")
    def handle_375(self, line: Line):
        self.motd.clear()
    @line_handler("375")
    @line_handler("372")
    def handle_372(self, line: Line):
        self.motd.append(line.params[1])

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
            if line.hostmask.username:
                self.username = line.hostmask.username
            if line.hostmask.hostname:
                self.hostname = line.hostmask.hostname

        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            user = self.get_user(line.hostmask.nickname)
            if line.hostmask.username:
                user.username = line.hostmask.username
            if line.hostmask.hostname:
                user.hostname = line.hostmask.hostname

            self.user_join(channel, user)

    def _handle_part(self, nickname, channel_name):
        channel_lower = self.casemap_lower(channel_name)
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            if self.casemap_equals(nickname, self.nickname):
                del self.channels[channel_lower]
                channel_users = self.channel_users.pop(channel)

                for user, cuser in channel_users.items():
                    self.user_channels[user].remove(channel)
                    if not self.user_channels[user]:
                        del self.user_channels[user]
                        del self.users[self.casemap_lower(user.nickname)]
            else:
                nickname_lower = self.casemap_lower(nickname)
                if nickname_lower in self.users:
                    user = self.users[nickname_lower]
                    self.user_channels[user].remove(channel)
                    if not self.user_channels[user]:
                        del self.users[nickname_lower]
                        del self.user_channels[user]
                    del self.channel_users[channel][user]

    @line_handler("PART")
    def handle_PART(self, line: Line):
        self._handle_part(line.hostmask.nickname, line.params[0])
    @line_handler("KICK")
    def handle_KICK(self, line: Line):
        self._handle_part(line.params[1], line.params[0])

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

    @line_handler("353")
    # channel's user list, "NAMES #channel" response (and on-join)
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

    @line_handler("329")
    # channel creation time, "MODE #channel" response (and on-join)
    def handle_329(self, line: Line):
        channel_lower = self.casemap_lower(line.params[1])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            channel.created = datetime.fromtimestamp(int(line.params[2]))

    @line_handler("TOPIC")
    def handle_TOPIC(self, line: Line):
        channel_lower = self.casemap_lower(line.params[0])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            channel.topic        = line.params[1]
            channel.topic_setter = str(line.hostmask)
            channel.topic_time   = datetime.utcnow()

    @line_handler("332")
    # topic text, "TOPIC #channel" response (and on-join)
    def handle_332(self, line: Line):
        channel_lower = self.casemap_lower(line.params[1])
        if channel_lower in self.channels:
            self.channels[channel_lower].topic = line.params[2]
    @line_handler("333")
    # topic setby, "TOPIC #channel" response (and on-join)
    def handle_333(self, line: Line):
        channel_lower = self.casemap_lower(line.params[1])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            channel.topic_setter = line.params[2]
            channel.topic_time   = datetime.fromtimestamp(int(line.params[3]))

    def _channel_modes(self,
            channel: Channel,
            modes: List[Tuple[bool, str]],
            params: List[str]):
        for add, char in modes:
            list_mode = char in self.isupport.chanmodes.list_modes
            if add and (
                    list_mode or
                    char in self.isupport.chanmodes.setting_b_modes or
                    char in self.isupport.chanmodes.setting_c_modes):
                channel.add_mode(char, params.pop(0), list_mode)
            elif not add and (
                    list_mode or
                    char in self.isupport.chanmodes.setting_b_modes):
                channel.remove_mode(char, params.pop(0))
            elif add:
                channel.add_mode(char, None, False)
            else:
                channel.remove_mode(char, None)

    @line_handler("MODE")
    def handle_MODE(self, line: Line):
        target     = line.params[0]
        modes_str  = line.params[1]
        params     = line.params[2:].copy()

        modifier                      = True
        modes: List[Tuple[bool, str]] = []

        for c in list(modes_str):
            if c == "+":
                modifier = True
            elif c == "-":
                modifier = False
            else:
                modes.append((modifier, c))

        if target == self.nickname:
            for add, char in modes:
                if add:
                    if not char in self.modes:
                        self.modes.append(char)
                elif char in self.modes:
                    self.modes.remove(char)
        elif self.has_channel(target):
            channel = self.channels[self.casemap_lower(target)]
            self._channel_modes(channel, modes, params)

    @line_handler("324")
    # channel modes, "MODE #channel" response (sometimes on-join?)
    def handle_324(self, line: Line):
        channel_lower = self.casemap_lower(line.params[1])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            modes   = [(True, char) for char in line.params[2].lstrip("+")]
            params  = line.params[3:]
            self._channel_modes(channel, modes, params)

    @line_handler("211")
    # our own user modes, "MODE nickname" response (sometimes on-connect?)
    def handle_211(self, line: Line):
        for char in line.params[1].lstrip("+"):
            if not char in self.modes:
                self.modes.append(char)

    @line_handler("PRIVMSG")
    def handle_PRIVMSG(self, line: Line):
        if line.hostmask.nickname == self.nickname:
            if line.hostmask.username:
                self.username = line.hostmask.username
            if line.hostmask.hostname:
                self.hostname = line.hostmask.hostname

        nickname_lower = self.casemap_lower(line.hostmask.nickname)
        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            if line.hostmask.username:
                user.username = line.hostmask.username
            if line.hostmask.hostname:
                user.hostname = line.hostmask.hostname

    @line_handler("396")
    # our own hostname, sometimes username@hostname, when it changes
    def handle_396(self, line: Line):
        username, _, hostname = line.params[1].rpartition("@")
        self.hostname = hostname
        if username:
            self.username = username

    @line_handler("352")
    # WHO line, "WHO #channel|nickname" response
    def handle_352(self, line: Line):
        nickname = line.params[5]
        username = line.params[2]
        hostname = line.params[3]
        realname = line.params[7].split(" ", 1)[1]

        if nickname == self.nickname:
            self.username = username
            self.hostname = hostname
            self.realname = realname

        nickname_lower = self.casemap_lower(line.params[5])
        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            user.username = username
            user.hostname = hostname
            user.realname = realname

    @line_handler("311")
    # WHOIS "user" line, one of "WHOIS nickname" response lines
    def handle_311(self, line: Line):
        nickname = line.params[1]
        username = line.params[2]
        hostname = line.params[3]
        realname = line.params[5]

        if nickname == self.nickname:
            self.username = username
            self.hostname = hostname
            self.realname = realname

        nickname_lower = self.casemap_lower(nickname)
        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            user.username = username
            user.hostname = hostname
            user.realname = realname

    @line_handler("CHGHOST")
    def handle_CHGHOST(self, line: Line):
        username = line.params[0]
        hostname = line.params[1]
        if line.hostmask.nickname == self.nickname:
            self.username = username
            self.hostname = hostname

        nickname_lower = self.casemap_lower(line.hostmask.nickname)
        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            user.username = username
            user.hostname = hostname

    @line_handler("CAP")
    def handle_CAP(self, line: Line):
        subcommand = line.params[1].upper()
        multiline  = line.params[2] == "*"
        caps       = line.params[2 + (1 if multiline else 0)]

        tokens: Dict[str, Optional[str]] = {}
        for cap in filter(bool, caps.split(" ")):
            key, _, value = cap.partition("=")
            tokens[key] = value or None

        if subcommand == "LS":
            self._temp_caps.update(tokens)
            if not multiline:
                self.caps = self._temp_caps.copy()
                self._temp_caps.clear()
        elif subcommand == "NEW":
            if not self.caps is None:
                self.caps.update(tokens)
        elif subcommand == "DEL":
            if not self.caps is None:
                for key in tokens.keys():
                    if key in self.caps.keys():
                        del self.caps[key]
                        if key in self.agreed_caps:
                            self.agreed_caps.remove(key)
        elif subcommand == "ACK":
            for key in tokens.keys():
                if key.startswith("-"):
                    key = key[1:]
                    if key in self.agreed_caps:
                        self.agreed_caps.remove(key)
                elif (not key in self.agreed_caps and
                        self.caps and
                        key in self.caps):
                    self.agreed_caps.append(key)
