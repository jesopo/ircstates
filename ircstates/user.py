from typing import Optional, Set
from .named import Named

class User(Named):
    nickname:       str
    nickname_lower: str

    def __init__(self):
        self.username: Optional[str] = None
        self.hostname: Optional[str] = None
        self.realname: Optional[str] = None
        self.account:  Optional[str] = None
        self.away:     Optional[str] = None
        self.channels: Set[str]      = set([])

    def __repr__(self) -> str:
        return f"User(nickname={self.nickname!r})"

    def set_nickname(self, nickname: str,
            nickname_lower: str):
        self.nickname       = nickname
        self.nickname_lower = nickname_lower

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
