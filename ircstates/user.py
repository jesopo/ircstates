from typing import Optional, Set
from .named import Named

class User(Named):
    nickname:       str
    nickname_lower: str

    def __init__(self, nickname: str, nickname_lower: str):
        self.set_nickname(nickname, nickname_lower)
        self.username: Optional[str] = None
        self.hostname: Optional[str] = None
        self.realname: Optional[str] = None
        self.account:  Optional[str] = None
        self.away:     Optional[str] = None

    def __repr__(self) -> str:
        return f"User(nickname={self.nickname!r})"

    def set_nickname(self, nickname: str,
            nickname_lower: str):
        self.nickname       = nickname
        self.nickname_lower = nickname_lower
