from typing import List, Optional
from .tokens import ChanModes, Prefix

class ISupport(object):
    chanmodes = ChanModes(["b"], ["k"], ["l"], ["i", "m", "n", "p", "s", "t"])
    prefix    = Prefix(["o", "v"], ["@", "+"])

    modes:       int = 3 # -1 if "no limit"
    casemapping: str = "rfc1459"
    chantypes:   List[str] = ["#"]

    def tokens(self, tokens: List[str]):
        for token in tokens:
            key, sep, value = token.partition("=")

            if key == "CHANMODES":
                a, b, c, d = value.split(",")
                self.chanmodes = ChanModes(list(a), list(b), list(c), list(d))

            elif key == "PREFIX":
                modes, prefixes = value[1:].split(")")
                self.prefix = Prefix(list(modes), list(prefixes))

            elif key == "MODES":
                self.modes = int(value) if value else -1

            elif key == "CASEMAPPING":
                self.casemapping = value

            elif key == "CHANTYPES":
                self.chantypes = list(value)
