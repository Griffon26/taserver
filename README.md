# taserver
A replacement implementation of the Tribes Ascend login server

This software allows anyone to host the servers that are needed to play Tribes Ascend 
multiplayer games. 

### Joining games

If you just want to join games on the login server hosted by me (Griffon26), then
you don't need to download anything. All you need to do is create a Windows shortcut to
`TribesAscend.exe` and add `-hostx=18.195.72.223` to the end of the target field, like this:

![Shortcut dialog](/docs/images/tashortcut.png?raw=true)

Start the game through the shortcut and log in with any name and password. The servers
listed in the server browser will be servers hosted by fellow players.

### Hosting a dedicated server

If you want to run a game server and have it show up in the server list for players who
connect to the replacement login server, follow these steps:

1. Get the code for [this project](https://github.com/Griffon26/taserver) from github

2. Download the latest `TAMods-Server.dll` (ask on the 
   [public Discord channel](https://discord.gg/8enekHQ) where to find it)

3. Modify `dir` under the `[gameserver]` section in `data/gameserverlauncher.ini` to point to 
   the directory where your TribesAscend.exe is located. For instance:

    ```
    C:\Games\Tribes Ascend\Binaries\Win32
    ```
    
4. Modify `controller_dll` under the `[gameserver]` section in `data/gameserverlauncher.ini` to 
   point to the downloaded TAMods-Server.dll.

5. Install python 3

6. Install the gevent module for python. From an administrator command prompt you should be able 
   to do it with:

    ```
    pip install gevent
    ```
    
   You may have to specify the full path. Something like:
   
    ```
    C:\Program Files (x86)\Python36\Scripts\pip install gevent
    ```

7. As administrator run `start_taserver_firewall.py` in the root of this repository. This is very 
   important. This script will manage firewall rules to keep kicked players out and only allow 
   logged in players on the game server. Without this script running you will not be able to get
   rid of hackers that are normally "unkickable".

8. Start the game server launcher by running the `start_game_server_launcher.py` script in the 
   root of this repository.

Your server should now show up in the list for anyone connecting to the login server.
Try it out by following the instructions under [Joining games](#joining-games)

### Running your own login server

Follow the steps for installation of python 
[Hosting a dedicated server](#hosting-a-dedicated-server), you can start the login server by
running  

1. Install python 3

2. Install the gevent module for python. From an administrator command prompt you should be able 
   to do it with:

    ```
    pip install gevent
    ```
    
   You may have to specify the full path. Something like:
   
    ```
    C:\Program Files (x86)\Python36\Scripts\pip install gevent
    ```

3. As administrator run `start_taserver_firewall.py` in the root of this repository. This is very 
   important if you want to make votekick work against "unkickable" hackers, but can be skipped
   if that does not interest you.

4. Start the login server by running the `start_login_server.py` script in the root of this 
   repository (preferably from a command window so you can read the errors if it exits for 
   some reason).

5. Change `host` under the `[loginserver]` section in `data/gameserverlauncher.ini` to 127.0.0.1
   if you want any [game server that you start](#hosting-a-dedicated-server) to connect to your
   locally running login server.   

## Limitations

In the past months we have worked hard to get to a version that has all required functionality
for a first usable release. If you encounter bugs or features that don't work yet, feel free
to [submit issues on this project](https://github.com/Griffon26/taserver/issues)  
