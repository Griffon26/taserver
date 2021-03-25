# Hosting multiple game servers on one machine

If your machine is powerful enough, you can also run multiple game servers on the same machine.
These instructions only describe the differences compared to running a single game server.
If you don't have your first game server running yet, then [get that up and running first](hosting_a_game_server.md). 

Running a second game server on the same machine can be achieved like this:

1. Make a copy of your taserver/data directory, such as taserver/data2

2. Modify the `serverconfig.lua` as appropriate (at least change the server description).

3. Open `shared.ini` for the new data directory and change `port_offset` to a low multiple of 2.
   (Setting this offset too high will cause port conflicts, so keep it under 90)   

4. Forward ports in your router as you did for the first game server, but include the `port_offset` that you chose.
    
    * 7777 + `port_offset` (UDP)
    * 7777 + `port_offset` (TCP)
    * 7778 + `port_offset` (UDP)
    * 7778 + `port_offset` (TCP)
    * 9002 + `port_offset` (UDP)
    
   So for instance if you set `port_offset` to 10, open up these ports: 

    * 7787/UDP
    * 7787/TCP
    * 7788/UDP
    * 7788/TCP
    * 9012/UDP
    
    **Do not manually open these ports in the firewall on the machine where the game server runs,
      otherwise votekick may not work correctly. taserver itself will manage the firewall rules**

5. To start the second server, use the `--data-root=/path/to/data2` flag for the firewall and game server launcher: in an administrator command prompt run `start_taserver_firewall.py --data-root=/path/to/data2`
   and from a second (non-administrator) command prompt run `start_game_server_launcher.py --data-root=path/to/data2`
   