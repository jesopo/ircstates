import string
from typing import List

ASCII_UPPER   = list(string.ascii_uppercase)
ASCII_LOWER   = list(string.ascii_lowercase)
RFC1459_UPPER = ASCII_UPPER+list("[]^\\")
RFC1459_LOWER = ASCII_LOWER+list("{}~|")

def _replace(s: str, upper: List[str], lower: List[str]):
    out = ""
    for char in s:
        if char in upper:
            out += lower[upper.index(char)]
        else:
            out += char
    return out

def casefold(mapping: str, s: str):
    if mapping   == "rfc1459":
        return _replace(s, RFC1459_UPPER, RFC1459_LOWER)
    elif mapping == "ascii":
        return _replace(s, ASCII_UPPER,   ASCII_LOWER)
