from typing import List, Optional
from .user import User
from .channel import Channel

class Emits(object):
    command: Optional[str] = None

    text:   Optional[str] = None

    self:        Optional[bool] = None
    self_source: Optional[bool] = None
    self_target: Optional[bool] = None

    user:        Optional[User] = None
    user_source: Optional[User] = None
    user_target: Optional[User] = None

    users: Optional[List[User]] = None

    channel:        Optional[Channel] = None
    channel_source: Optional[Channel] = None
    channel_target: Optional[Channel] = None

    target: Optional[str] = None
