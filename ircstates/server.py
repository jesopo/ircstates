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
from .numerics     import *

LINE_HANDLERS: Dict[str, List[Callable[["Server", Line], Emit]]] = {}
line_handler = handler_decorator(LINE_HANDLERS)

class ServerException(Exception):
    pass
class ServerDisconnectedException(ServerException):
    pass

WHO_TYPE = "524" # randomly generated

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

        self.registered = False
        self.modes: List[str] = []
        self.motd:  List[str] = []

        self._decoder = StatefulDecoder()

        self.users:         Dict[str, User]                        = {}
        self.channels:      Dict[str, Channel]                     = {}
        self.user_channels: Dict[User, Set[Channel]]               = {}
        self.channel_users: Dict[Channel, Dict[User, ChannelUser]] = {}

        self.isupport = ISupport()

        self.has_cap: bool = False
        self._temp_caps:     Dict[str, str] = {}
        self.available_caps: Dict[str, str] = {}
        self.agreed_caps:    List[str]      = []

    def __repr__(self) -> str:
        return f"Server(name={self.name!r})"

    def recv(self, data: bytes) -> List[Tuple[Line, List[Emit]]]:
        lines = self._decoder.push(data)
        if lines is None:
            raise ServerDisconnectedException()
        emits: List[List[Emit]] = []
        for line in lines:
            emits.append(self.parse_tokens(line))
        return list(zip(lines, emits))

    def parse_tokens(self, line: Line):
        emits: List[Emit] = []
        if line.command in LINE_HANDLERS:
            for callback in LINE_HANDLERS[line.command]:
                emit = callback(self, line)
                emit.command = line.command
                emits.append(emit)
        return emits

    def casefold(self, s1: str):
        return casefold(self.isupport.casemapping, s1)
    def casefold_equals(self, s1: str, s2: str):
        return self.casefold(s1) == self.casefold(s2)
    def is_me(self, nickname: str):
        return self.casefold(nickname) == self.nickname_lower

    def has_user(self, nickname: str) -> bool:
        return self.casefold(nickname) in self.users
    def _add_user(self, nickname: str, nickname_lower: str):
        user = self.create_user(nickname, nickname_lower)
        self.users[nickname_lower] = user

    def is_channel(self, target: str) -> bool:
        return target[:1] in self.isupport.chantypes
    def has_channel(self, name: str) -> bool:
        return self.casefold(name) in self.channels
    def get_channel(self, name: str) -> Optional[Channel]:
        return self.channels.get(self.casefold(name), None)

    def create_user(self, nickname: str, nickname_lower: str):
        return User(nickname, nickname_lower)
    def create_channel(self, name: str) -> Channel:
        return Channel(name)

    def _user_join(self, channel: Channel, user: User) -> ChannelUser:
        channel_user = ChannelUser(channel, user)
        if not user in self.user_channels:
            self.user_channels[user] =    set([])

        self.user_channels[user].add(channel)
        self.channel_users[channel][user] = channel_user
        return channel_user

    def prepare_whox(self, target: str) -> Line:
        return build("WHO", [target, f"n%ahinrtu,{WHO_TYPE}"])

    def _emit(self) -> Emit:
        return Emit()

    @line_handler(RPL_WELCOME)
    # first message reliably sent to us after registration is complete
    def _handle_welcome(self, line: Line) -> Emit:
        self.nickname = line.params[0]
        self.nickname_lower = self.casefold(line.params[0])
        self.registered = True
        return self._emit()

    @line_handler(RPL_ISUPPORT)
    # https://defs.ircdocs.horse/defs/isupport.html
    def _handle_ISUPPORT(self, line: Line) -> Emit:
        self.isupport.tokens(line.params[1:-1])
        return self._emit()

    @line_handler(RPL_MOTDSTART)
    # start of MOTD
    def _handle_motd_start(self, line: Line) -> Emit:
        self.motd.clear()
        return self._emit()
    @line_handler(RPL_MOTDSTART)
    # start of MOTD
    @line_handler(RPL_MOTD)
    # line of MOTD
    def _handle_motd_line(self, line: Line) -> Emit:
        emit = self._emit()
        text = line.params[1]
        emit.text = text
        self.motd.append(text)
        return emit

    @line_handler("NICK")
    def _handle_NICK(self, line: Line) -> Emit:
        new_nickname = line.params[0]
        nickname_lower = self.casefold(line.hostmask.nickname)

        emit = self._emit()

        if nickname_lower in self.users:
            user = self.users.pop(nickname_lower)
            emit.user = user

            new_nickname_lower = self.casefold(new_nickname)
            user._set_nickname(new_nickname, new_nickname_lower)
            self.users[new_nickname_lower] = user
        if nickname_lower == self.nickname_lower:
            emit.self = True

            self.nickname = new_nickname
            self.nickname_lower = self.casefold(new_nickname)
        return emit

    @line_handler("JOIN")
    def _handle_JOIN(self, line: Line) -> Emit:
        extended = len(line.params) == 3

        account = line.params[1].strip("*") if extended else None
        realname = line.params[2] if extended else None

        emit = self._emit()

        channel_lower = self.casefold(line.params[0])
        nickname_lower = self.casefold(line.hostmask.nickname)
        if nickname_lower == self.nickname_lower:
            emit.self = True
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
            emit.channel = channel
            if not nickname_lower in self.users:
                self._add_user(line.hostmask.nickname, nickname_lower)

            user = self.users[nickname_lower]
            emit.user = user
            if line.hostmask.username:
                user.username = line.hostmask.username
            if line.hostmask.hostname:
                user.hostname = line.hostmask.hostname
            if extended:
                user.account  = account
                user.realname = realname

            self._user_join(channel, user)
        return emit

    def _user_part(self, line: Line,
            nickname: str,
            channel_name: str,
            reason_i: int) -> Tuple[Emit, Optional[User]]:
        emit = self._emit()
        channel_lower = self.casefold(channel_name)
        reason = line.params[reason_i] if line.params[reason_i:] else None
        if not reason is None:
            emit.text = reason

        user: Optional[User] = None
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emit.channel = channel

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

        return emit, user

    @line_handler("PART")
    def _handle_PART(self, line: Line) -> Emit:
        emit, user = self._user_part(line, line.hostmask.nickname,
            line.params[0], 1)
        if not user is None:
            emit.user = user
            if user.nickname_lower == self.nickname_lower:
                emit.self = True
        return emit
    @line_handler("KICK")
    def _handle_KICK(self, line: Line) -> Emit:
        emit, kicked = self._user_part(line, line.params[1], line.params[0],
            2)
        if not kicked is None:
            emit.user_target = kicked

            if kicked.nickname_lower == self.nickname_lower:
                emit.self = True

            kicker_lower = self.casefold(line.hostmask.nickname)
            if kicker_lower == self.nickname_lower:
                emit.self_source = True

            if kicker_lower in self.users:
                emit.user_source = self.users[kicker_lower]
            else:
                emit.user_source = self.create_user(line.hostmask.nickname,
                    kicker_lower)

        return emit

    def _self_quit(self):
        self.users.clear()
        self.channels.clear()
        self.user_channels.clear()
        self.channel_users.clear()

    @line_handler("QUIT")
    def _handle_quit(self, line: Line) -> Emit:
        emit = self._emit()
        nickname_lower = self.casefold(line.hostmask.nickname)
        reason = line.params[0] if line.params else None
        if not reason is None:
            emit.text = reason

        if nickname_lower == self.nickname_lower:
            emit.self = True
            self._self_quit()
        else:
            if nickname_lower in self.users:
                user = self.users.pop(nickname_lower)
                emit.user = user
                for channel in self.user_channels[user]:
                    del self.channel_users[channel][user]
                del self.user_channels[user]
        return emit

    @line_handler("ERROR")
    def _handle_ERROR(self, line: Line) -> Emit:
        self._self_quit()
        return self._emit()

    @line_handler(RPL_NAMREPLY)
    # channel's user list, "NAMES #channel" response (and on-join)
    def _handle_names(self, line: Line) -> Emit:
        emit = self._emit()
        channel_lower = self.casefold(line.params[2])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emit.channel = channel
            nicknames = list(filter(bool, line.params[3].split(" ")))
            users: List[User] = []
            emit.users = users

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
        return emit

    @line_handler(RPL_CREATIONTIME)
    # channel creation time, "MODE #channel" response (and on-join)
    def _handle_creation_time(self, line: Line) -> Emit:
        emit = self._emit()
        channel_lower = self.casefold(line.params[1])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emit.channel = channel
            channel.created = datetime.fromtimestamp(int(line.params[2]))
        return emit

    @line_handler("TOPIC")
    def _handle_TOPIC(self, line: Line) -> Emit:
        emit = self._emit()
        channel_lower = self.casefold(line.params[0])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emit.channel = channel
            channel.topic        = line.params[1]
            channel.topic_setter = str(line.hostmask)
            channel.topic_time   = datetime.utcnow()
        return emit

    @line_handler(RPL_TOPIC)
    # topic text, "TOPIC #channel" response (and on-join)
    def _handle_topic_num(self, line: Line) -> Emit:
        emit = self._emit()
        channel_lower = self.casefold(line.params[1])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emit.channel = channel
            self.channels[channel_lower].topic = line.params[2]
        return emit
    @line_handler(RPL_TOPICWHOTIME)
    # topic setby, "TOPIC #channel" response (and on-join)
    def _handle_topic_time(self, line: Line) -> Emit:
        emit = self._emit()
        channel_lower = self.casefold(line.params[1])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emit.channel = channel
            channel.topic_setter = line.params[2]
            channel.topic_time   = datetime.fromtimestamp(int(line.params[3]))
        return emit

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
    def _handle_MODE(self, line: Line) -> Emit:
        emit = self._emit()
        target     = line.params[0]
        modes_str  = line.params[1]
        params     = line.params[2:].copy()

        modifier                      = "+"
        modes: List[Tuple[bool, str]] = []
        tokens: List[str]             = []

        for c in list(modes_str):
            if c in ["+", "-"]:
                modifier = c
            else:
                add = modifier == "+"
                modes.append((add, c))
                tokens.append(f"{modifier}{c}")
        emit.tokens = tokens

        target_lower = self.casefold(target)
        if target_lower == self.nickname_lower:
            emit.self_target = True
            for add, char in modes:
                if add:
                    if not char in self.modes:
                        self.modes.append(char)
                elif char in self.modes:
                    self.modes.remove(char)
        elif target_lower in self.channels:
            channel = self.channels[self.casefold(target)]
            emit.channel = channel
            self._channel_modes(channel, modes, params)
        return emit

    @line_handler(RPL_CHANNELMODEIS)
    # channel modes, "MODE #channel" response (sometimes on-join?)
    def _handle_channelmodeis(self, line: Line) -> Emit:
        emit = self._emit()
        channel_lower = self.casefold(line.params[1])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emit.channel = channel
            modes   = [(True, char) for char in line.params[2].lstrip("+")]
            params  = line.params[3:]
            self._channel_modes(channel, modes, params)
        return emit

    @line_handler(RPL_UMODEIS)
    # our own user modes, "MODE nickname" response (sometimes on-connect?)
    def _handle_umodeis(self, line: Line) -> Emit:
        for char in line.params[1].lstrip("+"):
            if not char in self.modes:
                self.modes.append(char)
        return self._emit()

    @line_handler("PRIVMSG")
    @line_handler("NOTICE")
    @line_handler("TAGMSG")
    def _handle_message(self, line: Line) -> Emit:
        emit = self._emit()
        message = line.params[1] if line.params[1:] else None
        if not message is None:
            emit.text = message

        nickname_lower = self.casefold(line.hostmask.nickname)
        if nickname_lower == self.nickname_lower:
            emit.self_source = True
            if line.hostmask.username:
                self.username = line.hostmask.username
            if line.hostmask.hostname:
                self.hostname = line.hostmask.hostname

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
        else:
            user = self.create_user(line.hostmask.nickname, nickname_lower)
        emit.user = user

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
        emit.target = target_raw

        target_lower = self.casefold(target)
        if self.is_channel(target):
            if target_lower in self.channels:
                channel = self.channels[target_lower]
                emit.channel = channel
        elif target_lower == self.nickname_lower:
            emit.self_target = True
        return emit

    @line_handler(RPL_VISIBLEHOST)
    # our own hostname, sometimes username@hostname, when it changes
    def _handle_visiblehost(self, line: Line) -> Emit:
        username, _, hostname = line.params[1].rpartition("@")
        self.hostname = hostname
        if username:
            self.username = username
        return self._emit()

    @line_handler(RPL_WHOREPLY)
    # WHO line, "WHO #channel|nickname" response
    def _handle_who(self, line: Line) -> Emit:
        emit = self._emit()
        emit.target = line.params[1]
        nickname = line.params[5]
        username = line.params[2]
        hostname = line.params[3]
        realname = line.params[7].split(" ", 1)[1]

        nickname_lower = self.casefold(line.params[5])
        if nickname_lower == self.nickname_lower:
            emit.self = True
            self.username = username
            self.hostname = hostname
            self.realname = realname

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            emit.user = user
            user.username = username
            user.hostname = hostname
            user.realname = realname
        return emit

    @line_handler(RPL_WHOSPCRPL)
    # WHOX line, "WHO #channel|nickname" response; only listen for our "type"
    def _handle_whox(self, line: Line) -> Emit:
        emit = self._emit()
        if line.params[1] == WHO_TYPE and len(line.params) == 8:
            nickname_lower = self.casefold(line.params[5])
            username = line.params[2]
            hostname = line.params[4]
            realname = line.params[7]

            account: Optional[str] = None
            if not line.params[6] == "0":
                account = line.params[6]

            if nickname_lower in self.users:
                user = self.users[nickname_lower]
                emit.user = user
                user.username = username
                user.hostname = hostname
                user.realname = realname
                user.account  = account
            if nickname_lower == self.nickname_lower:
                emit.self = True
                self.username = username
                self.hostname = hostname
                self.realname = realname
                self.account  = account

        return emit

    @line_handler(RPL_WHOISUSER)
    # WHOIS "user" line, one of "WHOIS nickname" response lines
    def _handle_whoisuser(self, line: Line) -> Emit:
        emit = self._emit()
        nickname = line.params[1]
        username = line.params[2]
        hostname = line.params[3]
        realname = line.params[5]

        nickname_lower = self.casefold(nickname)
        if nickname_lower == self.nickname_lower:
            emit.self = True
            self.username = username
            self.hostname = hostname
            self.realname = realname

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            emit.user = user
            user.username = username
            user.hostname = hostname
            user.realname = realname
        return emit

    @line_handler("CHGHOST")
    def _handle_CHGHOST(self, line: Line) -> Emit:
        emit = self._emit()
        username = line.params[0]
        hostname = line.params[1]
        nickname_lower = self.casefold(line.hostmask.nickname)
        if nickname_lower == self.nickname_lower:
            emit.self = True
            self.username = username
            self.hostname = hostname

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            emit.user = user
            user.username = username
            user.hostname = hostname
        return emit

    @line_handler("SETNAME")
    def _handle_SETNAME(self, line: Line) -> Emit:
        emit = self._emit()
        realname = line.params[0]
        nickname_lower = self.casefold(line.hostmask.nickname)
        if nickname_lower == self.nickname_lower:
            emit.self = True
            self.realname = realname

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            emit.user = user
            user.realname = realname
        return emit

    @line_handler("AWAY")
    def _handle_AWAY(self, line: Line) -> Emit:
        emit = self._emit()
        away = line.params[0] if line.params else None
        nickname_lower = self.casefold(line.hostmask.nickname)
        if nickname_lower == self.nickname_lower:
            emit.self = True
            self.away = away

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            emit.user = user
            user.away = away
        return emit

    @line_handler("ACCOUNT")
    def _handle_ACCOUNT(self, line: Line) -> Emit:
        emit = self._emit()
        account = line.params[0].strip("*")
        nickname_lower = self.casefold(line.hostmask.nickname)
        if nickname_lower == self.nickname_lower:
            emit.self = True
            self.account = account

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            emit.user = user
            user.account = account
        return emit

    @line_handler("CAP")
    def _handle_CAP(self, line: Line) -> Emit:
        self.has_cap = True
        subcommand = line.params[1].upper()
        multiline  = line.params[2] == "*"
        caps       = line.params[2 + (1 if multiline else 0)]


        tokens:     Dict[str, str] = {}
        tokens_str: List[str]      = []
        for cap in filter(bool, caps.split(" ")):
            tokens_str.append(cap)
            key, _, value = cap.partition("=")
            tokens[key] = value

        emit = self._emit()
        emit.subcommand = subcommand
        emit.finished   = not multiline
        emit.tokens     = tokens_str

        if subcommand == "LS":
            self._temp_caps.update(tokens)
            if not multiline:
                self.available_caps = self._temp_caps.copy()
                self._temp_caps.clear()
        elif subcommand == "NEW":
            self.available_caps.update(tokens)
        elif subcommand == "DEL":
            for key in tokens.keys():
                if key in self.available_caps.keys():
                    del self.available_caps[key]
                    if key in self.agreed_caps:
                        self.agreed_caps.remove(key)
        elif subcommand == "ACK":
            for key in tokens.keys():
                if key.startswith("-"):
                    key = key[1:]
                    if key in self.agreed_caps:
                        self.agreed_caps.remove(key)
                elif (not key in self.agreed_caps and
                        key in self.available_caps):
                    self.agreed_caps.append(key)
        return emit
