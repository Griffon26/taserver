# Running your own login server

Running your own login server is usually not needed. When you start a game server using
[these instructions](hosting_a_game_server.md) it will connect to the default login 
server running on `ta.kfk4ever.com` (`18.197.240.229`). Your server will show up in the list 
for anyone else connecting to this login server.

One scenario where you would want to run your own login server is when you want to play
on a LAN disconnected from the internet. In that case, follow these steps to set it up:

1. Install the **x86 version** of the
   [Visual C++ Redistributable for Visual Studio 2015](https://www.microsoft.com/en-us/download/details.aspx?id=48145).
   It contains `msvcp140.dll`, which is needed by TAMods-Server and the UDP proxy used by the
   firewall script.

2. Install python 3

3. Install the gevent and certifi modules for python. From an administrator command prompt you should be able 
   to do it with:

    ```
    pip install -r requirements.txt
    ```
    
   You may have to specify the full path. Something like:
   
    ```
    C:\Program Files (x86)\Python36\Scripts\pip install -r requirements.txt
    ```

4. Open an administrator command prompt and go to the directory containing the taserver files

5. Run the `download_udpproxy.py` script to download the `udpproxy.exe` program used by the 
   taserver firewall script. This is a precompiled version of the C++ source code in the `udpproxy`
   subdirectory.
   
6. As administrator run `start_taserver_firewall.py` in the root of this repository. This is very 
   important if you want to make votekick work against "unkickable" hackers, but can be skipped
   if that does not interest you.

7. If the login server is running behind a router you'll need to forward the following ports to
   the login server:
    
   * 9000/TCP
   * 9001/TCP
   * 9080/TCP
   
   **Do not manually open these ports in the firewall on the machine where the login server runs,
     otherwise votekick may not work correctly. taserver itself will manage the firewall rules**

8. Open a second command prompt (doesn't need to be an administrator one) and go to the
   directory containing the taserver files

9. Start the login server by running the `start_login_server.py` script in the root of this 
   repository.

10. Change `host` under the `[loginserver]` section in `data/gameserverlauncher.ini` to `127.0.0.1`
   to have any [game server that you start](hosting_a_game_server.md) connect to your locally
   running login server. Note: setting `host` to `127.0.0.1` will prevent anyone else from
   connecting to your game server. For LAN play you should set `host` to the LAN IP of the computer
   running the login server. If you want people on the internet to join you can try setting `host` 
   to your external IP instead, but it depends on your network setup/hardware if this will work. 
