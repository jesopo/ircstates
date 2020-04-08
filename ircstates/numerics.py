NUMERIC_NUMBERS = {}
NUMERIC_NAMES = {}

def _numeric(number: str, name: str):
    NUMERIC_NUMBERS[number] = name
    NUMERIC_NAMES[name]     = number

_numeric("001", "RPL_WELCOME")
_numeric("005", "RPL_ISUPPORT")
_numeric("372", "RPL_MOTD")
_numeric("375", "RPL_MOTDSTART")
_numeric("221", "RPL_UMODEIS")
_numeric("396", "RPL_VISIBLEHOST")

_numeric("324", "RPL_CHANNELMODEIS")
_numeric("329", "RPL_CREATIONTIME")
_numeric("332", "RPL_TOPIC")
_numeric("333", "RPL_TOPICWHOTIME")

_numeric("352", "RPL_WHOREPLY")
_numeric("353", "RPL_NAMREPLY")
_numeric("366", "RPL_ENDOFNAMES")

_numeric("903", "RPL_SASLSUCCESS")
_numeric("904", "ERR_SASLFAIL")
_numeric("905", "ERR_SASLTOOLONG")
_numeric("906", "ERR_SASLABORTED")
_numeric("907", "ERR_SASLALREADY")
_numeric("908", "RPL_SASLMECHS")

_numeric("311", "RPL_WHOISUSER")
_numeric("312", "RPL_WHOISSERVER")
_numeric("313", "RPL_WHOISOPERATOR")
_numeric("317", "RPL_WHOISIDLE")
_numeric("319", "RPL_WHOISCHANNELS")
_numeric("330", "RPL_WHOISACCOUNT")
_numeric("378", "RPL_WHOISHOST")
_numeric("379", "RPL_WHOISMODES")
_numeric("671", "RPL_WHOISSECURE")
_numeric("318", "RPL_ENDOFWHOIS")
