from enum import Enum
from string import ascii_lowercase, ascii_uppercase
from typing import Dict, List

class CaseMap(Enum):
    ASCII = "ascii"
    RFC1459 = "rfc1459"

def _make_trans(upper: str, lower: str):
    return str.maketrans(dict(zip(upper, lower)))

CASEMAPS: Dict[CaseMap, Dict[int, str]] = {
    CaseMap.ASCII: _make_trans(
        r"ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        r"abcdefghijklmnopqrstuvwxyz"
    ),
    CaseMap.RFC1459: _make_trans(
        r"ABCDEFGHIJKLMNOPQRSTUVWXYZ\[]^",
        r"abcdefghijklmnopqrstuvwxyz|{}~"
    )
}
def casefold(casemap_name: CaseMap, s: str):
    casemap = CASEMAPS[casemap_name]
    return s.translate(casemap)
