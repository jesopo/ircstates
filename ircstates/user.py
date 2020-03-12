from typing import Optional, Set
from .named import Named

class User(Named):
    def __init__(self, nickname: str):
        self.nickname = nickname

    def set_nickname(self, nickname: str,
            nickname_lower: str):
        self.nickname = nickname
        self.name =     nickname_lower
