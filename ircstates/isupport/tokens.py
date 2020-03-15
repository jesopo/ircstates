from typing import List, Optional

class ChanModes(object):
    def __init__(self,
            list_modes:      List[str],
            setting_b_modes: List[str],
            setting_c_modes: List[str],
            setting_d_modes: List[str]):

        self.list_modes      =  list_modes
        self.setting_b_modes = setting_b_modes
        self.setting_c_modes = setting_c_modes
        self.setting_d_modes = setting_d_modes

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
