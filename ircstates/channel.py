from typing   import Dict, List, Optional, Set
from pendulum import DateTime

from .named        import Named
from .channel_user import ChannelUser

class Channel(Named):
    name_lower: str
    def __init__(self):
        self.users: Dict[str, ChannelUser] = {}

        self.topic:        Optional[str]      = None
        self.topic_setter: Optional[str]      = None
        self.topic_time:   Optional[DateTime] = None

        self.created:      Optional[DateTime] = None

        self.list_modes:   Dict[str, List[str]]     = {}
        self.modes:        Dict[str, Optional[str]] = {}

    def __repr__(self) -> str:
        return f"Channel(name={self.name!r})"

    def set_name(self, name: str, name_lower: str):
        self.name       = name
        self.name_lower = name_lower

    def add_mode(self,
            char: str,
            param: Optional[str],
            list_mode: bool):
        if list_mode:
            if not char in self.list_modes:
                self.list_modes[char] = []
            if not param in self.list_modes[char]:
                self.list_modes[char].append(param or "")
        else:
            self.modes[char] = param

    def remove_mode(self,
            char: str,
            param: Optional[str]):
        if char in self.list_modes:
            if param in self.list_modes[char]:
                self.list_modes[char].remove(param)
                if not self.list_modes[char]:
                    del self.list_modes[char]
        elif char in self.modes:
            del self.modes[char]
