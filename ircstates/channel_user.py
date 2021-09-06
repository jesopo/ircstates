from typing   import List, Optional, Set
from .names   import Name
from pendulum import DateTime, now

class ChannelUser(object):
    def __init__(self,
            nickname: Name,
            channel_name: Name):
        self._nickname     = nickname
        self._channel_name = channel_name

        self.modes:  Set[str] = set()
        self.since = now("utc")
        self.joined: Optional[DateTime] = None

    def __repr__(self) -> str:
        outs: List[str] = [self.channel, self.nickname]
        if self.modes:
            outs.append(f"+{''.join(self.modes)}")
        return f"ChannelUser({' '.join(outs)})"

    @property
    def nickname(self) -> str:
        return self._nickname.normal
    @property
    def nickname_lower(self) -> str:
        return self._nickname.folded

    @property
    def channel(self) -> str:
        return self._channel_name.normal
