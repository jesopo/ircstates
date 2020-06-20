from typing import List, Optional
from dataclasses import dataclass

@dataclass
class ChanModes(object):
    a_modes: List[str]
    b_modes: List[str]
    c_modes: List[str]
    d_modes: List[str]

class Prefix(object):
    def __init__(self,
            modes:    List[str],
            prefixes: List[str]):
        self.modes    = modes
        self.prefixes = prefixes

    def from_mode(self, mode: str) -> Optional[str]:
        if mode in self.modes:
            return self.prefixes[self.modes.index(mode)]
        return None
    def from_prefix(self, prefix: str) -> Optional[str]:
        if prefix in self.prefixes:
            return self.modes[self.prefixes.index(prefix)]
        return None
