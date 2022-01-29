from enum import Enum
from string import ascii_lowercase, ascii_uppercase
from typing import Dict, List, Optional

class CaseMap(Enum):
    ASCII = "ascii"
    RFC1459 = "rfc1459"

CASEMAPS: Dict[CaseMap, Dict[int, Optional[int]]] = {
    CaseMap.ASCII: str.maketrans(
        r"ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        r"abcdefghijklmnopqrstuvwxyz"
    ),
    CaseMap.RFC1459: str.maketrans(
        r"ABCDEFGHIJKLMNOPQRSTUVWXYZ\[]^",
        r"abcdefghijklmnopqrstuvwxyz|{}~"
    )
}
def casefold(casemap_name: CaseMap, s: str):
    casemap = CASEMAPS[casemap_name]
    return s.translate(casemap)
