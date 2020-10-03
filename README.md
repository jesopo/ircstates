# ircstates

[![Build Status](https://travis-ci.org/jesopo/ircstates.svg?branch=master)](https://travis-ci.org/jesopo/ircstates)

## rationale

I wanted a bare-bones reference implementation of taking byte input, parsing it
into tokens and then managing an IRC client session state from it.

with this library, you can have client session state managed for you and put
additional arbitrary functionality on top of it.


## usage

### simple

```python
import ircstates

server = ircstates.Server("freenode")
lines  = server.recv(b":server 001 nick :hello world!\r\n")
lines += server.recv(b":nick JOIN #chan\r\n")
for line in lines:
    server.parse_tokens(line)

chan = server.channels["#chan"]
```

### socket to state

```python
import ircstates, irctokens, socket

NICK = "nickname"
CHAN = "#chan"
HOST = "127.0.0.1"
PORT = 6667

server  = ircstates.Server("freenode")
sock    = socket.socket()

sock.connect((HOST, PORT))
def _send(raw: str):
    sock.sendall(f"{raw}\r\n".encode("utf8"))

_send("USER test 0 * test")
_send(f"NICK {NICK}")

while True:
    recv_data  = sock.recv(1024)
    recv_lines = server.recv(recv_data)
    for line in recv_lines:
        server.parse_tokens(line)
        print(f"< {line.format()}")

        # user defined behaviors...
        if line.command == "PING":
            _send(f"PONG :{line.params[0]}")
```

### get a user's channels
```python
>>> server.users
{'nickname': User(nickname='nickname')}
>>> user = server.users["nickname"]
>>> user
User(nickname='nickname')
>>> user.channels
{'#chan'}
```

### get a channel's users
```python
>>> server.channels
{'#chan': Channel(name='#chan')}
>>> channel = server.channels["#chan"]
>>> channel
Channel(name='#chan')
>>> channel.users
{'jess': ChannelUser(#chan jess)}
```

### get a user's modes in channel
```python
>>> channel = server.channels["#chan"]
>>> channel_user = channel.users["nickname"]
>>> channel_user
ChannelUser(#chan jess +ov)
>>> channel_user.modes
{'o', 'v'}
```

## contact

Come say hi at [##irctokens on freenode](https://webchat.freenode.net/?channels=%23%23irctokens)
