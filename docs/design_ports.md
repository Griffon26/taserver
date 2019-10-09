# Used UDP/TCP ports

The diagram below shows which parts of taserver are using which UDP and TCP ports.
Connections that are not to localhost require port forwarding if the destination host
is behind a router.

The reason that this diagram shows two game servers is that during a map switch there
are two servers running simultaneously. For this to be possible these servers cannot
use the same ports.

The source of the diagram is contained in the PNG file. To edit it go to https://www.draw.io/
and load the PNG file.

![Ports design](design_ports.png?raw=true)
