from typing    import Callable, Dict, List, Optional, Set, Tuple
from datetime  import datetime
from irctokens import build, Hostmask, Line, StatefulDecoder, StatefulEncoder

from .named        import Named
from .user         import User
from .channel      import Channel
from .channel_user import ChannelUser
from .isupport     import ISupport
from .decorators   import handler_decorator
from .casemap      import casefold
from .emit         import *

LINE_HANDLERS: Dict[str, List[Callable[["Server", Line], Emits]]] = {}
line_handler = handler_decorator(LINE_HANDLERS)

class ServerException(Exception):
    pass
class ServerDisconnectedException(ServerException):
    pass

class Server(Named):
    def __init__(self, name: str):
        self.name = name

        self.nickname                = ""
        self.nickname_lower          = ""
        self.username: Optional[str] = None
        self.hostname: Optional[str] = None
        self.realname: Optional[str] = None
        self.account:  Optional[str] = None
        self.away:     Optional[str] = None

        self.modes: List[str] = []
        self.motd:  List[str] = []

        self._decoder = StatefulDecoder()

        self.users:         Dict[str, User]                        = {}
        self.channels:      Dict[str, Channel]                     = {}
        self.user_channels: Dict[User, Set[Channel]]               = {}
        self.channel_users: Dict[Channel, Dict[User, ChannelUser]] = {}

        self.isupport = ISupport()

        self._temp_caps:  Dict[str, Optional[str]]           = {}
        self.caps:        Optional[Dict[str, Optional[str]]] = None
        self.agreed_caps: List[str]                          = []

    def __repr__(self) -> str:
        return f"Server(name={self.name!r})"

    def recv(self, data: bytes) -> List[Tuple[Line, List[Emits]]]:
        lines = self._decoder.push(data)
        if lines is None:
            raise ServerDisconnectedException()
        emits: List[List[Emits]] = []
        for line in lines:
            emits.append(self.parse_tokens(line))
        return list(zip(lines, emits))

    def parse_tokens(self, line: Line):
        all_emits: List[Emits] = []
        if line.command in LINE_HANDLERS:
            for callback in LINE_HANDLERS[line.command]:
                emits = callback(self, line)
                emits.command = line.command
                all_emits.append(emits)
        return all_emits

    def casefold(self, s1: str):
        return casefold(self.isupport.casemapping, s1)
    def casefold_equals(self, s1: str, s2: str):
        return self.casefold(s1) == self.casefold(s2)

    def has_user(self, nickname: str) -> bool:
        return self.casefold(nickname) in self.users
    def create_user(self, nickname: str, nickname_lower: str):
        return User(nickname, nickname_lower)
    def _add_user(self, nickname: str, nickname_lower: str):
        user = self.create_user(nickname, nickname_lower)
        self.users[nickname_lower] = user

    def is_channel(self, target: str) -> bool:
        return target[:1] in self.isupport.chantypes
    def has_channel(self, name: str) -> bool:
        return self.casefold(name) in self.channels
    def create_channel(self, name: str) -> Channel:
        return Channel(name)
    def get_channel(self, name: str) -> Optional[Channel]:
        return self.channels.get(self.casefold(name), None)

    def _user_join(self, channel: Channel, user: User) -> ChannelUser:
        channel_user = ChannelUser(channel, user)
        if not user in self.user_channels:
            self.user_channels[user] =    set([])

        self.user_channels[user].add(channel)
        self.channel_users[channel][user] = channel_user
        return channel_user

    def _emit(self) -> Emits:
        return Emits()

    @line_handler("001")
    # first message reliably sent to us after registration is complete
    def _handle_001(self, line: Line):
        self.nickname = line.params[0]
        self.nickname_lower = self.casefold(line.params[0])
        return self._emit()

    @line_handler("005")
    # https://defs.ircdocs.horse/defs/isupport.html
    def _handle_ISUPPORT(self, line: Line):
        self.isupport.tokens(line.params[1:-1])
        return self._emit()

    @line_handler("375")
    # start of MOTD
    def _handle_375(self, line: Line):
        self.motd.clear()
        return self._emit()
    @line_handler("375")
    # start of MOTD
    @line_handler("372")
    # line of MOTD
    def _handle_372(self, line: Line):
        emits = self._emit()
        text = line.params[1]
        emits.text = text
        self.motd.append(text)
        return emits

    @line_handler("NICK")
    def _handle_NICK(self, line: Line):
        new_nickname = line.params[0]
        nickname_lower = self.casefold(line.hostmask.nickname)

        emits = self._emit()

        if nickname_lower in self.users:
            user = self.users.pop(nickname_lower)
            emits.user = user

            new_nickname_lower = self.casefold(new_nickname)
            user._set_nickname(new_nickname, new_nickname_lower)
            self.users[new_nickname_lower] = user
        if nickname_lower == self.nickname_lower:
            emits.self = True

            self.nickname = new_nickname
            self.nickname_lower = self.casefold(new_nickname)
        return emits

    @line_handler("JOIN")
    def _handle_JOIN(self, line: Line):
        extended = len(line.params) == 3

        account = line.params[1].strip("*") if extended else None
        realname = line.params[2] if extended else None

        emits = self._emit()

        channel_lower = self.casefold(line.params[0])
        nickname_lower = self.casefold(line.hostmask.nickname)
        if nickname_lower == self.nickname_lower:
            emits.self = True
            if not channel_lower in self.channels:
                channel = self.create_channel(line.params[0])
                self.channels[channel_lower] = channel
                self.channel_users[channel] = {}
            if line.hostmask.username:
                self.username = line.hostmask.username
            if line.hostmask.hostname:
                self.hostname = line.hostmask.hostname
            if extended:
                self.account  = account
                self.realname = realname

        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emits.channel = channel
            if not nickname_lower in self.users:
                self._add_user(line.hostmask.nickname, nickname_lower)

            user = self.users[nickname_lower]
            emits.user = user
            if line.hostmask.username:
                user.username = line.hostmask.username
            if line.hostmask.hostname:
                user.hostname = line.hostmask.hostname
            if extended:
                user.account  = account
                user.realname = realname

            self._user_join(channel, user)
        return emits

    def _user_part(self, line: Line,
            nickname: str,
            channel_name: str,
            reason_i: int) -> Tuple[Emits, Optional[User]]:
        emits = self._emit()
        channel_lower = self.casefold(channel_name)
        reason = line.params[reason_i] if line.params[reason_i:] else None
        if not reason is None:
            emits.text = reason

        user: Optional[User] = None
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emits.channel = channel

            nickname_lower = self.casefold(nickname)
            if nickname_lower in self.users:
                user = self.users[nickname_lower]
                user = user
                self.user_channels[user].remove(channel)
                if not self.user_channels[user]:
                    del self.users[nickname_lower]
                    del self.user_channels[user]
                del self.channel_users[channel][user]

            if nickname_lower == self.nickname_lower:
                del self.channels[channel_lower]
                channel_users = self.channel_users.pop(channel)

                for user, cuser in channel_users.items():
                    self.user_channels[user].remove(channel)
                    if not self.user_channels[user]:
                        del self.user_channels[user]
                        del self.users[self.casefold(user.nickname)]

        return emits, user

    @line_handler("PART")
    def _handle_PART(self, line: Line):
        emits, user = self._user_part(line, line.hostmask.nickname,
            line.params[0], 1)
        if not user is None:
            emits.user = user
            if user.nickname_lower == self.nickname_lower:
                emits.self = True
        return emits
    @line_handler("KICK")
    def _handle_KICK(self, line: Line):
        emits, kicked = self._user_part(line, line.params[1], line.params[0],
            2)
        if not kicked is None:
            emits.user_target = kicked

            if kicked.nickname_lower == self.nickname_lower:
                emits.self = True

            kicker_lower = self.casefold(line.hostmask.nickname)
            if kicker_lower == self.nickname_lower:
                emits.self_source = True

            if kicker_lower in self.users:
                emits.user_source = self.users[kicker_lower]
            else:
                emits.user_source = self.create_user(line.hostmask.nickname,
                    kicker_lower)

        return emits

    def _self_quit(self):
        self.users.clear()
        self.channels.clear()
        self.user_channels.clear()
        self.channel_users.clear()

    @line_handler("QUIT")
    def _handle_quit(self, line: Line):
        emits = self._emit()
        nickname_lower = self.casefold(line.hostmask.nickname)
        reason = line.params[0] if line.params else None
        if not reason is None:
            emits.text = reason

        if nickname_lower == self.nickname_lower:
            emits.self = True
            self._self_quit()
        else:
            if nickname_lower in self.users:
                user = self.users.pop(nickname_lower)
                emits.user = user
                for channel in self.user_channels[user]:
                    del self.channel_users[channel][user]
                del self.user_channels[user]
        return emits

    @line_handler("ERROR")
    def _handle_ERROR(self, line: Line):
        self._self_quit()
        return self._emit()

    @line_handler("353")
    # channel's user list, "NAMES #channel" response (and on-join)
    def _handle_353(self, line: Line):
        emits = self._emit()
        channel_lower = self.casefold(line.params[2])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emits.channel = channel
            nicknames = list(filter(bool, line.params[3].split(" ")))
            users: List[User] = []
            emits.users = users

            for nickname in nicknames:
                modes = ""
                for char in nickname:
                    mode = self.isupport.prefix.from_prefix(char)
                    if mode:
                        modes += mode
                    else:
                        break

                hostmask = Hostmask.from_source(nickname[len(modes):])
                nickname_lower = self.casefold(hostmask.nickname)
                if not nickname_lower in self.users:
                    self._add_user(hostmask.nickname, nickname_lower)
                user = self.users[nickname_lower]
                users.append(user)
                channel_user = self._user_join(channel, user)

                if hostmask.username:
                    user.username = hostmask.username
                    if nickname_lower == self.nickname_lower:
                        self.username = hostmask.username
                if hostmask.hostname:
                    user.hostname = hostmask.hostname
                    if nickname_lower == self.nickname_lower:
                        self.hostname = hostmask.hostname


                for mode in modes:
                    if not mode in channel_user.modes:
                        channel_user.modes.append(mode)
        return emits

    @line_handler("329")
    # channel creation time, "MODE #channel" response (and on-join)
    def _handle_329(self, line: Line):
        emits = self._emit()
        channel_lower = self.casefold(line.params[1])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emits.channel = channel
            channel.created = datetime.fromtimestamp(int(line.params[2]))
        return emits

    @line_handler("TOPIC")
    def _handle_TOPIC(self, line: Line):
        emits = self._emit()
        channel_lower = self.casefold(line.params[0])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emits.channel = channel
            channel.topic        = line.params[1]
            channel.topic_setter = str(line.hostmask)
            channel.topic_time   = datetime.utcnow()
        return emits

    @line_handler("332")
    # topic text, "TOPIC #channel" response (and on-join)
    def _handle_332(self, line: Line):
        emits = self._emit()
        channel_lower = self.casefold(line.params[1])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emits.channel = channel
            self.channels[channel_lower].topic = line.params[2]
        return emits
    @line_handler("333")
    # topic setby, "TOPIC #channel" response (and on-join)
    def _handle_333(self, line: Line):
        emits = self._emit()
        channel_lower = self.casefold(line.params[1])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emits.channel = channel
            channel.topic_setter = line.params[2]
            channel.topic_time   = datetime.fromtimestamp(int(line.params[3]))
        return emits

    def _channel_modes(self,
            channel: Channel,
            modes: List[Tuple[bool, str]],
            params: List[str]):
        for add, char in modes:
            list_mode = char in self.isupport.chanmodes.list_modes
            if char in self.isupport.prefix.modes:
                nickname_lower = self.casefold(params.pop(0))
                if nickname_lower in self.users:
                    user = self.users[nickname_lower]
                    channel_user = self.channel_users[channel][user]
                    if add:
                        if not char in channel_user.modes:
                            channel_user.modes.append(char)
                    elif char in channel_user.modes:
                        channel_user.modes.remove(char)
            elif add and (
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
    def _handle_MODE(self, line: Line):
        emits = self._emit()
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

        target_lower = self.casefold(target)
        if target_lower == self.nickname_lower:
            emits.self_target = True
            for add, char in modes:
                if add:
                    if not char in self.modes:
                        self.modes.append(char)
                elif char in self.modes:
                    self.modes.remove(char)
        elif target_lower in self.channels:
            channel = self.channels[self.casefold(target)]
            emits.channel = channel
            self._channel_modes(channel, modes, params)
        return emits

    @line_handler("324")
    # channel modes, "MODE #channel" response (sometimes on-join?)
    def _handle_324(self, line: Line):
        emits = self._emit()
        channel_lower = self.casefold(line.params[1])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emits.channel = channel
            modes   = [(True, char) for char in line.params[2].lstrip("+")]
            params  = line.params[3:]
            self._channel_modes(channel, modes, params)
        return emits

    @line_handler("211")
    # our own user modes, "MODE nickname" response (sometimes on-connect?)
    def _handle_211(self, line: Line):
        for char in line.params[1].lstrip("+"):
            if not char in self.modes:
                self.modes.append(char)
        return self._emit()

    @line_handler("PRIVMSG")
    @line_handler("NOTICE")
    @line_handler("TAGMSG")
    def _handle_message(self, line: Line):
        emits = self._emit()
        message = line.params[1] if line.params[1:] else None
        if not message is None:
            emits.text = message

        nickname_lower = self.casefold(line.hostmask.nickname)
        if nickname_lower == self.nickname_lower:
            emits.self_source = True
            if line.hostmask.username:
                self.username = line.hostmask.username
            if line.hostmask.hostname:
                self.hostname = line.hostmask.hostname

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
        else:
            user = self.create_user(line.hostmask.nickname, nickname_lower)
        emits.user = user

        if line.hostmask.username:
            user.username = line.hostmask.username
        if line.hostmask.hostname:
            user.hostname = line.hostmask.hostname

        target_raw = target = line.params[0]
        statusmsg = []
        while target:
            if target[0] in self.isupport.statusmsg:
                statusmsg.append(target[0])
                target = target[1:]
            else:
                break
        emits.target = target_raw

        target_lower = self.casefold(target)
        if self.is_channel(target):
            if target_lower in self.channels:
                channel = self.channels[target_lower]
                emits.channel = channel
        elif target_lower == self.nickname_lower:
            emits.self_target = True
        return emits

    @line_handler("396")
    # our own hostname, sometimes username@hostname, when it changes
    def _handle_396(self, line: Line):
        username, _, hostname = line.params[1].rpartition("@")
        self.hostname = hostname
        if username:
            self.username = username
        return self._emit()

    @line_handler("352")
    # WHO line, "WHO #channel|nickname" response
    def _handle_352(self, line: Line):
        emits = self._emit()
        emits.target = line.params[1]
        nickname = line.params[5]
        username = line.params[2]
        hostname = line.params[3]
        realname = line.params[7].split(" ", 1)[1]

        nickname_lower = self.casefold(line.params[5])
        if nickname_lower == self.nickname_lower:
            emits.self = True
            self.username = username
            self.hostname = hostname
            self.realname = realname

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            emits.user = user
            user.username = username
            user.hostname = hostname
            user.realname = realname
        return emits

    @line_handler("311")
    # WHOIS "user" line, one of "WHOIS nickname" response lines
    def _handle_311(self, line: Line):
        emits = self._emit()
        nickname = line.params[1]
        username = line.params[2]
        hostname = line.params[3]
        realname = line.params[5]

        nickname_lower = self.casefold(nickname)
        if nickname_lower == self.nickname_lower:
            emits.self = True
            self.username = username
            self.hostname = hostname
            self.realname = realname

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            emits.user = user
            user.username = username
            user.hostname = hostname
            user.realname = realname
        return emits

    @line_handler("CHGHOST")
    def _handle_CHGHOST(self, line: Line):
        emits = self._emit()
        username = line.params[0]
        hostname = line.params[1]
        nickname_lower = self.casefold(line.hostmask.nickname)
        if nickname_lower == self.nickname_lower:
            emits.self = True
            self.username = username
            self.hostname = hostname

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            emits.user = user
            user.username = username
            user.hostname = hostname
        return emits

    @line_handler("SETNAME")
    def _handle_SETNAME(self, line: Line):
        emits = self._emit()
        realname = line.params[0]
        nickname_lower = self.casefold(line.hostmask.nickname)
        if nickname_lower == self.nickname_lower:
            emits.self = True
            self.realname = realname

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            emits.user = user
            user.realname = realname
        return emits

    @line_handler("AWAY")
    def _handle_AWAY(self, line: Line):
        emits = self._emit()
        away = line.params[0] if line.params else None
        nickname_lower = self.casefold(line.hostmask.nickname)
        if nickname_lower == self.nickname_lower:
            emits.self = True
            self.away = away

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            emits.user = user
            user.away = away
        return emits

    @line_handler("ACCOUNT")
    def _handle_ACCOUNT(self, line: Line):
        emits = self._emit()
        account = line.params[0].strip("*")
        nickname_lower = self.casefold(line.hostmask.nickname)
        if nickname_lower == self.nickname_lower:
            emits.self = True
            self.account = account

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            emits.user = user
            user.account = account
        return emits

    @line_handler("CAP")
    def _handle_CAP(self, line: Line):
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
        return self._emit()
