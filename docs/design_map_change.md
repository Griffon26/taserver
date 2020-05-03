Upon map change a new server is started on a different port and clients are 
transferred to this server when it is ready. This document describes the steps
in this process.

The source of the diagram is contained in the PNG file. To edit it go to https://www.draw.io/
and load the PNG file.

![Ports design](design_map_change.png?raw=true)

1. the launcher uses two ports for running game servers 7777 and 7778. Only one of 
   these ports will generally be in use at a time.

2. the controller of a server sends a match end message with controller_context and a list of
   maps that can be voted for when the match ends. The controller guarantees that this is the
   last message that it will send.
   
3. the launcher launches a new server on the unused port

4. the new controller instance will connect to the launcher and send a protocol version message

5. the launcher will notify the login server that the game controller is ready to start loading
   the next map
   
6. the login server will reply with a message containing the highest-voted map ID

5. the launcher will put that map ID in the controller_context and send it to
   the new controller instance, which can then start loading the map

6. when receiving match time from the new server, the launcher will send a server-ready
   message containing the port of the new server to the login server

7. when the login server receives the server-ready message it will:
   * send a message to all clients on the old server to reconnect to the different port
   * set the server to joinable if it wasn't already
   * send a next map message to the launcher
   
8. when receiving the next map message the launcher will stop the old server and mark
   the new one as the active server

At the moment the time between the end of a match and the switch to the new server is
determined by how long it takes the new server to get ready; the login server could delay
its response to the "waiting for map" message, but it does not do so at the moment.
If in the future we implement the match summary screen, we'll probably change this.
