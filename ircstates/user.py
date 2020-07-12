from typing import Optional, Set
from .names import Name

class User(object):
    def __init__(self, nickname: Name):
        self._nickname = nickname

        self.username: Optional[str] = None
        self.hostname: Optional[str] = None
        self.realname: Optional[str] = None
        self.account:  Optional[str] = None
        self.server:   Optional[str] = None
        self.away:     Optional[str] = None
        self.ip:       Optional[str] = None
        self.channels: Set[str]      = set([])

    def __repr__(self) -> str:
        return f"User(nickname={self.nickname!r})"

    def get_name(self) -> Name:
        return self._nickname
    @property
    def nickname(self) -> str:
        return self._nickname.normal
    @property
    def nickname_lower(self) -> str:
        return self._nickname.folded

    def change_nickname(self,
            normal: str,
            folded: str):
        self._nickname.normal = normal
        self._nickname.folded = folded

    def hostmask(self) -> str:
        hostmask = self.nickname
        if self.username is not None:
            hostmask += f"!{self.username}"
        if self.hostname is not None:
            hostmask += f"@{self.hostname}"
        return hostmask

    def userhost(self) -> Optional[str]:
        if (self.username is not None and
                self.hostname is not None):
            return f"{self.username}@{self.hostname}"
        else:
            return None
