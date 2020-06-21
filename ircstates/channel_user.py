from typing import List
from .names import Name

class ChannelUser(object):
    def __init__(self,
            nickname: Name,
            channel_name: Name):
        self._nickname     = nickname
        self._channel_name = channel_name

        self.modes: List[str] = []

    @property
    def nickname(self) -> str:
        return self._nickname.normal
    @property
    def nickname_lower(self) -> str:
        return self._nickname.folded
