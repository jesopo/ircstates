from datetime import datetime
from typing import Dict, List, Optional, Set
from .named import Named

class Channel(Named):
    def __init__(self, name: str):
        self.name = name

        self.topic:        Optional[str]      = None
        self.topic_setter: Optional[str]      = None
        self.topic_time:   Optional[datetime] = None

        self.list_modes:   Dict[str, List[str]] = {}
        self.modes:        Dict[str, str]       = {}
