# Connection handler design

The connection handler module was made to make it easier for programs
such as the game server launcher and login server to communicate with 
other programs over the internet.

The above programs are organized around a central task that waits until
a message is put in its gevent queue, processes the message and waits 
for the next message.

The following diagram shows how code based on the connection handler
module can work together with this central task for processing messages
from a remote host.

![PlantUML model](http://www.plantuml.com/plantuml/png/5Sqn3i8m34RXdLF01MA9WO6f6yUeWkCsaPBVbUt0zIdJDxpXBHxPOev-kJLmdqMczMkDEFn9PFcRzXPrlgUBiI84aLW7lQnjc-B-eCXd-eZHo1udHTcfYBSTAoiW74snrepInTBnVos2Sle3)  

### The ConnectionHandler class

There is a subclass of `ConnectionHandler` for incoming connections and
one for outgoing connections. For incoming connections the address and 
port specify the local interface and port to listen on, for outgoing 
connections it is the remote host address and port instead.

When a connection is established a `PeerConnected` message containing an
instance of a `Peer` subclass is put in the incoming queue. The 
`ConnectionHandler` will put this `Peer` instance in the `peer` member 
variable of every message from this peer that is put in the incoming queue.

### Adding a connection handler

Handling a new type of connection requires creating subclasses of:

* `ConnectionReader` (or its subclass `TcpMessageConnectionReader`)
* `ConnectionWriter` (or its subclass `TcpMessageConnectionWriter`)
* `Peer`
* either `IncomingConnectionHandler` or `OutgoingConnectionHandler`

If you subclass from `ConnectionWriter` you will have to implement 
the `encode` and `send` methods. If you use `TcpMessageConnectionWriter`
you only need to implement `encode`. `send` will send the message
bytes in chunks of the `max_message_size`, each preceded by a 16-bit short
indicating length (0 when equal to `max_message_size`). This simple 
packet structure will probably suffice for most connections.

The same holds for `ConnectionReader` and `TcpMessageConnectionReader`
and the `receive` and `decode` methods.

The `Peer` subclass can be left empty, but it has to be a subclass so
it can be used to distinguish between connections from different 
connection handlers. 

The abstract method `create_connection_instances` of `Incoming/OutgoingConnectionHandler`
should return instances of the above subclasses and will be called once
for each established connection.

For more details take a look at the connection handler implementations in these files:

* `game_server_launcher/gamecontrollerhandler.py` (for a single incoming connection)
* `game_server_launcher/loginserverhandler.py` (for a single outgoing connection)   
* `login_server/gameserverlauncherhandler.py` (for multiple incoming connections)
