from typing import Dict, List, Optional
from .tokens import ChanModes, Prefix

CASEMAPPINGS = ["rfc1459", "ascii"]

class ISupport(object):
    raw: Dict[str, Optional[str]]

    network: Optional[str] = None

    chanmodes = ChanModes(["b"], ["k"], ["l"], ["i", "m", "n", "p", "s", "t"])
    prefix    = Prefix(["o", "v"], ["@", "+"])

    modes:       int       = 3 # -1 if "no limit"
    casemapping: str       = "rfc1459"
    chantypes:   List[str] = ["#"]
    statusmsg:   List[str] = []

    callerid: Optional[str] = None
    excepts:  Optional[str] = None
    invex:    Optional[str] = None

    monitor: Optional[int] = None # -1 if "no limit"
    watch:   Optional[int] = None # -1 if "no limit"
    whox:    bool          = False

    def __init__(self):
        self.raw = {}

    def from_tokens(self, tokens: List[str]):
        for token in tokens:
            key, sep, value = token.partition("=")
            self.raw[key] = value if sep else None

            if   key == "NETWORK":
                self.network = value

            elif key == "CHANMODES":
                a, b, c, d = value.split(",")
                self.chanmodes = ChanModes(list(a), list(b), list(c), list(d))

            elif key == "PREFIX":
                modes, prefixes = value[1:].split(")")
                self.prefix = Prefix(list(modes), list(prefixes))

            elif key == "STATUSMSG":
                self.statusmsg = list(value)

            elif key == "MODES":
                self.modes   = int(value) if value else -1
            elif key == "MONITOR":
                self.monitor = int(value) if value else -1
            elif key == "WATCH":
                self.watch   = int(value) if value else -1

            elif key == "CASEMAPPING":
                if value in CASEMAPPINGS:
                    self.casemapping = value

            elif key == "CHANTYPES":
                self.chantypes = list(value)

            elif key == "CALLERID":
                self.callerid = value or "g"
            elif key == "EXCEPTS":
                self.excepts  = value or "e"
            elif key == "INVEX":
                self.invex    = value or "I"

            elif key == "WHOX":
                self.whox = True
