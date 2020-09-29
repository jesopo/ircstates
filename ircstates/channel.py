from typing   import Dict, List, Optional, Set
from pendulum import DateTime

from .channel_user import ChannelUser
from .names        import Name

class Channel(object):
    def __init__(self, name: Name):
        self._name = name

        self.users: Dict[str, ChannelUser] = {}

        self.topic:        Optional[str]      = None
        self.topic_setter: Optional[str]      = None
        self.topic_time:   Optional[DateTime] = None

        self.created:      Optional[DateTime] = None

        self._list_modes_temp: Dict[str, List[str]]     = {}
        self.list_modes:       Dict[str, List[str]]     = {}
        self.modes:            Dict[str, Optional[str]] = {}

    def __repr__(self) -> str:
        return f"Channel(name={self.name!r})"

    def get_name(self) -> Name:
        return self._name
    @property
    def name(self) -> str:
        return self._name.normal
    @property
    def name_lower(self) -> str:
        return self._name.folded

    def add_mode(self,
            char: str,
            param: Optional[str],
            list_mode: bool):
        if list_mode:
            if param is not None:
                if not char in self.list_modes:
                    self.list_modes[char] = []
                if not param in self.list_modes[char]:
                    self.list_modes[char].append(param)
        else:
            self.modes[char] = param

    def remove_mode(self,
            char: str,
            param: Optional[str]):
        if char in self.list_modes:
            if (param is not None and
                    param in self.list_modes[char]):
                self.list_modes[char].remove(param)
        elif char in self.modes:
            del self.modes[char]
