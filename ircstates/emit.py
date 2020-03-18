from .user import User
from .channel import Channel

class Emit(object):
    def __eq__(self, other):
        return repr(self) == repr(other)

class EmitCommand(Emit):
    def __init__(self, command: str):
        self.command = command
    def __repr__(self) -> str:
        return f"EmitCommand({self.command})"

class EmitSelf(Emit):
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
class EmitSourceSelf(EmitSelf):
    pass
class EmitTargetSelf(EmitSelf):
    pass

class EmitText(Emit):
    def __init__(self, text: str):
        self.text = text
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.text!r})"

class EmitUser(Emit):
    def __init__(self, user: User):
        self.user = user
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.user.nickname!r})"
class EmitSourceUser(EmitUser):
    pass
class EmitTargetUser(EmitSourceUser):
    pass

class EmitChannel(Emit):
    def __init__(self, channel: Channel):
        self.channel = channel
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.channel.name!r})"
class EmitSourceChannel(EmitChannel):
    pass
class EmitTargetChannel(EmitChannel):
    pass

class EmitTarget(Emit):
    def __init__(self, target: str):
        self.target = target
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.target!r})"

