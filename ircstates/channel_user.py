from typing import List
from .names import Name

class ChannelUser(object):
    def __init__(self,
            nickname: Name,
            channel_name: Name):
        self._nickname     = nickname
        self._channel_name = channel_name

        self.modes: List[str] = []

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
