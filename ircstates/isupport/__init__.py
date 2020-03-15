from typing import Dict, List, Optional
from .tokens import ChanModes, Prefix

CASEMAPPINGS = ["rfc1459", "ascii"]

class ISupport(object):
    raw: Dict[str, Optional[str]]

    chanmodes = ChanModes(["b"], ["k"], ["l"], ["i", "m", "n", "p", "s", "t"])
    prefix    = Prefix(["o", "v"], ["@", "+"])

    modes:       int = 3 # -1 if "no limit"
    casemapping: str = "rfc1459"
    chantypes:   List[str] = ["#"]

    def __init__(self):
        self.raw = {}

    def tokens(self, tokens: List[str]):
        for token in tokens:
            key, sep, value = token.partition("=")
            self.raw[key] = value if sep else None

            if key == "CHANMODES":
                a, b, c, d = value.split(",")
                self.chanmodes = ChanModes(list(a), list(b), list(c), list(d))

            elif key == "PREFIX":
                modes, prefixes = value[1:].split(")")
                self.prefix = Prefix(list(modes), list(prefixes))

            elif key == "MODES":
                self.modes = int(value) if value else -1

            elif key == "CASEMAPPING":
                if value in CASEMAPPINGS:
                    self.casemapping = value

            elif key == "CHANTYPES":
                self.chantypes = list(value)
