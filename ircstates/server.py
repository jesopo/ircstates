from ipaddress import ip_address
from typing    import Callable, Dict, List, Optional, Set, Tuple
from irctokens import Line, build, Hostmask, StatefulDecoder, StatefulEncoder
from irctokens import hostmask as hostmask_
from pendulum  import from_timestamp, now

from .user         import User
from .channel      import Channel
from .channel_user import ChannelUser
from .isupport     import ISupport
from .decorators   import handler_decorator
from .casemap      import casefold
from .names        import Name
from .emit         import *
from .numerics     import *

LINE_HANDLERS: Dict[str, List[Callable[["Server", Line], Emit]]] = {}
line_handler = handler_decorator(LINE_HANDLERS)

class ServerException(Exception):
    pass
class ServerDisconnectedException(ServerException):
    pass

WHO_TYPE = "735" # randomly generated
TYPE_EMIT = Optional[Emit]

class Server(object):
    def __init__(self, name: str):
        self.name = name

        self.nickname                = ""
        self.nickname_lower          = ""
        self.username: Optional[str] = None
        self.hostname: Optional[str] = None
        self.realname: Optional[str] = None
        self.account:  Optional[str] = None
        self.server:   Optional[str] = None
        self.away:     Optional[str] = None
        self.ip:       Optional[str] = None

        self.registered = False
        self.modes: List[str] = []
        self.motd:  List[str] = []

        self._decoder = StatefulDecoder()

        self.users:    Dict[str, User]    = {}
        self.channels: Dict[str, Channel] = {}

        self.isupport = ISupport()

        self.has_cap: bool = False
        self._temp_caps:     Dict[str, str] = {}
        self.available_caps: Dict[str, str] = {}
        self.agreed_caps:    List[str]      = []

    def __repr__(self) -> str:
        return f"Server(name={self.name!r})"

    def recv(self, data: bytes) -> List[Line]:
        lines = self._decoder.push(data)
        if lines is None:
            raise ServerDisconnectedException()
        return lines

    def parse_tokens(self, line: Line) -> TYPE_EMIT:
        ret_emit: TYPE_EMIT = None
        if line.command in LINE_HANDLERS:
            for callback in LINE_HANDLERS[line.command]:
                emit = callback(self, line)
                if emit is not None and ret_emit is None:
                    emit.command = line.command
                    ret_emit = emit
        return ret_emit

    def casefold(self, s1: str):
        return casefold(self.isupport.casemapping, s1)
    def casefold_equals(self, s1: str, s2: str):
        return self.casefold(s1) == self.casefold(s2)
    def is_me(self, nickname: str):
        return self.casefold(nickname) == self.nickname_lower

    def has_user(self, nickname: str) -> bool:
        return self.casefold(nickname) in self.users
    def _add_user(self, nickname: str, nickname_lower: str):
        user = self.create_user(Name(nickname, nickname_lower))
        self.users[nickname_lower] = user

    def is_channel(self, target: str) -> bool:
        return target[:1] in self.isupport.chantypes
    def has_channel(self, name: str) -> bool:
        return self.casefold(name) in self.channels
    def get_channel(self, name: str) -> Optional[Channel]:
        return self.channels.get(self.casefold(name), None)

    def create_user(self, nickname: Name) -> User:
        return User(nickname)

    def create_channel(self, name: Name) -> Channel:
        return Channel(name)

    def _user_join(self, channel: Channel, user: User) -> ChannelUser:
        channel_user = ChannelUser(
            user.get_name(),
            channel.get_name())

        user.channels.add(self.casefold(channel.name))
        channel.users[user.nickname_lower] = channel_user
        return channel_user

    def prepare_whox(self, target: str) -> Line:
        return build("WHO", [target, f"n%afhinrstu,{WHO_TYPE}"])

    def _self_hostmask(self, hostmask: Hostmask):
        self.nickname = hostmask.nickname
        if hostmask.username:
            self.username = hostmask.username
        if hostmask.hostname:
            self.hostname = hostmask.hostname

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
        self.isupport.from_tokens(line.params[1:-1])
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
        new_nickname       = line.params[0]
        new_nickname_lower = self.casefold(new_nickname)
        nickname_lower     = self.casefold(line.hostmask.nickname)

        emit = self._emit()

        if nickname_lower in self.users:
            user = self.users.pop(nickname_lower)
            emit.user = user
            user.change_nickname(new_nickname, new_nickname_lower)
            self.users[new_nickname_lower] = user

            for channel_lower in user.channels:
                channel = self.channels[channel_lower]
                channel_user = channel.users.pop(nickname_lower)
                channel.users[user.nickname_lower] = channel_user

        if nickname_lower == self.nickname_lower:
            emit.self = True

            self.nickname       = new_nickname
            self.nickname_lower = new_nickname_lower
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
                channel = self.create_channel(
                    Name(line.params[0], channel_lower)
                )
                #TODO: put this somewhere better
                for mode in self.isupport.chanmodes.a_modes:
                    channel.list_modes[mode] = []

                self.channels[channel_lower] = channel

            self._self_hostmask(line.hostmask)
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

                user.channels.remove(channel.name_lower)
                del channel.users[user.nickname_lower]
                if not user.channels:
                    del self.users[nickname_lower]

            if nickname_lower == self.nickname_lower:
                del self.channels[channel_lower]

                for key, cuser in channel.users.items():
                    ruser = self.users[key]
                    ruser.channels.remove(channel.name_lower)
                    if not ruser.channels:
                        del self.users[ruser.nickname_lower]

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
                emit.user_source = self.create_user(
                    Name(line.hostmask.nickname, kicker_lower)
                )

        return emit

    def _self_quit(self):
        self.users.clear()
        self.channels.clear()

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
                for channel_lower in user.channels:
                    channel = self.channels[channel_lower]
                    del channel.users[user.nickname_lower]
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

                hostmask = hostmask_(nickname[len(modes):])
                nickname_lower = self.casefold(hostmask.nickname)
                if not nickname_lower in self.users:
                    self._add_user(hostmask.nickname, nickname_lower)
                user = self.users[nickname_lower]
                users.append(user)
                channel_user = self._user_join(channel, user)

                if hostmask.username:
                    user.username = hostmask.username
                if hostmask.hostname:
                    user.hostname = hostmask.hostname

                if nickname_lower == self.nickname_lower:
                    self._self_hostmask(hostmask)

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
            channel.created = from_timestamp(int(line.params[2]))
        return emit

    @line_handler("TOPIC")
    def _handle_TOPIC(self, line: Line) -> Emit:
        emit = self._emit()
        channel_lower = self.casefold(line.params[0])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emit.channel = channel
            channel.topic        = line.params[1]
            channel.topic_setter = line.source
            channel.topic_time   = now("utc")
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
            channel.topic_time   = from_timestamp(int(line.params[3]))
        return emit

    def _channel_modes(self,
            channel: Channel,
            modes: List[str],
            params: List[str]
            ) -> List[Tuple[str, Optional[str]]]:
        tokens: List[Tuple[str, Optional[str]]] = []

        for mode in modes:
            add  = mode[0] == "+"
            char = mode[1]
            arg: Optional[str] = None

            if char in self.isupport.prefix.modes: # a user's status
                arg = params.pop(0)
                nickname_lower = self.casefold(arg)

                if nickname_lower in self.users:
                    user = self.users[nickname_lower]
                    channel_user = channel.users[user.nickname_lower]
                    if add:
                        if not char in channel_user.modes:
                            channel_user.modes.append(char)
                    elif char in channel_user.modes:
                        channel_user.modes.remove(char)
            else:
                has_arg = False
                is_list = False
                if char in self.isupport.chanmodes.a_modes:
                    has_arg = True
                    is_list = True
                elif add:
                    has_arg = char in (self.isupport.chanmodes.b_modes+
                        self.isupport.chanmodes.c_modes)
                else: # remove
                    has_arg = char in self.isupport.chanmodes.b_modes

                if has_arg:
                    arg = params.pop(0)

                if add:
                    channel.add_mode(char, arg, is_list)
                else:
                    channel.remove_mode(char, arg)

            tokens.append((mode, arg))

        return tokens

    @line_handler("MODE")
    def _handle_MODE(self, line: Line) -> Emit:
        emit = self._emit()
        target     = line.params[0]
        modes_str  = line.params[1]
        params     = line.params[2:].copy()

        modifier          = "+"
        modes: List[str]  = []

        for c in list(modes_str):
            if c in ["+", "-"]:
                modifier = c
            else:
                modes.append(f"{modifier}{c}")

        target_lower = self.casefold(target)
        if target_lower == self.nickname_lower:
            emit.self_target = True
            emit.tokens = modes

            for mode in modes:
                add  = mode[0] == "+"
                char = mode[1]
                if add:
                    if not char in self.modes:
                        self.modes.append(char)
                elif char in self.modes:
                    self.modes.remove(char)
        elif target_lower in self.channels:
            channel = self.channels[self.casefold(target)]
            emit.channel = channel
            ctokens = self._channel_modes(channel, modes, params)

            ctokens_str: List[str] = []
            for mode, arg in ctokens:
                if arg is not None:
                    ctokens_str.append(f"{mode} {arg}")
                else:
                    ctokens_str.append(mode)
            emit.tokens = ctokens_str
        return emit

    @line_handler(RPL_CHANNELMODEIS)
    # channel modes, "MODE #channel" response (sometimes on-join?)
    def _handle_channelmodeis(self, line: Line) -> Emit:
        emit = self._emit()
        channel_lower = self.casefold(line.params[1])
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            emit.channel = channel
            modes   = [f"+{char}" for char in line.params[2].lstrip("+")]
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

    def _mode_list(self,
            channel_name: str,
            mode: str,
            mask: str):
        channel_lower = self.casefold(channel_name)
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            if not mode in channel._list_modes_temp:
                channel._list_modes_temp[mode] = []
            channel._list_modes_temp[mode].append(mask)
    def _mode_list_end(self,
            channel_name: str,
            mode: str):
        channel_lower = self.casefold(channel_name)
        if channel_lower in self.channels:
            channel = self.channels[channel_lower]
            if mode in channel._list_modes_temp:
                mlist = channel._list_modes_temp.pop(mode)
                channel.list_modes[mode] = mlist

    @line_handler(RPL_BANLIST)
    def _handle_banlist(self, line: Line) -> Emit:
        channel = line.params[1]
        mask    = line.params[2]

        if len(line.params) > 3:
            # parse these out but we're not storing them yet
            set_by  = line.params[3]
            set_at  = int(line.params[4])

        self._mode_list(channel, "b", mask)
        return self._emit()

    @line_handler(RPL_ENDOFBANLIST)
    def _handle_banlist_end(self, line: Line) -> Emit:
        channel = line.params[1]
        self._mode_list_end(channel, "b")
        return self._emit()

    @line_handler(RPL_QUIETLIST)
    def _handle_quietlist(self, line: Line) -> Emit:
        channel = line.params[1]
        mode    = line.params[2]
        mask    = line.params[3]
        set_by  = line.params[4]
        set_at  = int(line.params[5])

        self._mode_list(channel, mode, mask)
        return self._emit()

    @line_handler(RPL_ENDOFQUIETLIST)
    def _handle_quietlist_end(self, line: Line) -> Emit:
        channel = line.params[1]
        mode    = line.params[2]
        self._mode_list_end(channel, mode)
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
            self._self_hostmask(line.hostmask)

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
        else:
            user = self.create_user(
                Name(line.hostmask.nickname, nickname_lower)
            )
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
        status   = line.params[6]
        away     = "" if "G" in status else None
        realname = line.params[7].split(" ", 1)[1]

        server:  Optional[str] = None
        if not line.params[4] == "*":
            server  = line.params[4]

        nickname_lower = self.casefold(line.params[5])
        if nickname_lower == self.nickname_lower:
            emit.self = True
            self.username = username
            self.hostname = hostname
            self.realname = realname
            self.server   = server
            self.away     = away

        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            emit.user = user
            user.username = username
            user.hostname = hostname
            user.realname = realname
            user.server   = server
            user.away     = away
        return emit

    @line_handler(RPL_WHOSPCRPL)
    # WHOX line, "WHO #channel|nickname" response; only listen for our "type"
    def _handle_whox(self, line: Line) -> Emit:
        emit = self._emit()
        if line.params[1] == WHO_TYPE and len(line.params) == 10:
            nickname_lower = self.casefold(line.params[6])
            username = line.params[2]
            hostname = line.params[4]
            status   = line.params[7]
            away     = "" if "G" in status else None
            realname = line.params[9]

            account: Optional[str] = None
            if not line.params[8] == "0":
                account = line.params[8]
            server:  Optional[str] = None
            if not line.params[5] == "*":
                server  = line.params[5]
            ip:      Optional[str] = None
            if not line.params[3] == "255.255.255.255":
                try:
                    ip = ip_address(line.params[3]).compressed
                except ValueError:
                    pass

            if nickname_lower in self.users:
                user = self.users[nickname_lower]
                emit.user = user
                user.username = username
                user.hostname = hostname
                user.realname = realname
                user.account  = account
                user.server   = server
                user.away     = away
                if ip is not None:
                    user.ip   = ip

            if nickname_lower == self.nickname_lower:
                emit.self = True
                self.username = username
                self.hostname = hostname
                self.realname = realname
                self.account  = account
                self.server   = server
                self.away     = away
                if ip is not None:
                    self.ip   = ip

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

    @line_handler(RPL_AWAY)
    # sent in response to a command directed at a user who is marked as away
    def _handle_RPL_AWAY(self, line: Line) -> Emit:
        nickname       = line.params[1]
        nickname_lower = self.casefold(nickname)
        reason         = line.params[2]

        if nickname_lower == self.nickname_lower:
            self.away = reason
        if nickname_lower in self.users:
            user = self.users[nickname_lower]
            user.away = reason

        return self._emit()

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

    @line_handler(RPL_LOGGEDIN)
    def _handle_loggedin(self, line: Line) -> Emit:
        hostmask_str = line.params[1]
        hostmask     = hostmask_(hostmask_str)
        account      = line.params[2]

        self.account = account
        self._self_hostmask(hostmask)
        return self._emit()

    @line_handler(RPL_LOGGEDOUT)
    def _handle_loggedout(self, line: Line) -> Emit:
        hostmask_str = line.params[1]
        hostmask     = hostmask_(hostmask_str)

        self.account = None
        self._self_hostmask(hostmask)
        return self._emit()
