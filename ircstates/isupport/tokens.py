from typing import List, Optional

class ChanModes(object):
    def __init__(self,
            a_modes: List[str],
            b_modes: List[str],
            c_modes: List[str],
            d_modes: List[str]):
        self.a_modes = a_modes
        self.b_modes = b_modes
        self.c_modes = c_modes
        self.d_modes = d_modes

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
