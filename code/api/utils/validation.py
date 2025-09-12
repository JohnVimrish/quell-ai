import re
from typing import Iterable

def contains_sensitive(text: str, patterns: Iterable[str]) -> bool:
    for p in patterns:
        if re.search(p, text, flags=re.IGNORECASE):
            return True
    return False
