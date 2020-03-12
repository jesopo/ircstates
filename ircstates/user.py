from typing import Optional, Set
from .named import Named

class User(Named):
    nickname: Optional[str]

    def __init__(self):
        self.nickanme: Optional[str] = None

    def set_nickname(self, nickname: str,
            nickname_lower: str):
        self.nickname = nickname
        self.name =     nickname_lower
