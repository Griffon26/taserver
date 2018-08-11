# taserver
A replacement implementation of the Tribes Ascend login server

## How to use it
If you do decide to try it out, here's how.

1. Get the code for this project from github

2. Modify `dir` under the `[gameserver]` section in `data/gameserverlauncher.ini` to point to the directory where your TribesAscend.exe is located. For instance:

    ```
    C:\Games\Tribes Ascend\Binaries\Win32
    ```
  
3. Create a shortcut to TribesAscend.exe with the following command line for starting a client that will connect to the login server running on your own machine:

    ```
    TribesAscend.exe -hostx=127.0.0.1
    ```
3. Install python 3

4. Install the gevent module for python. From an administrator command prompt you should be able to do it with:

    ```
    pip install gevent
    ```
   You may have to specify the full path. Something like:
   
    ```
    C:\Program Files (x86)\Python36\Scripts\pip install gevent
    ```

5. Start the login server by running the `start_login_server.py` script in the root of this repository (preferably from a command window so you can read the errors if it exits for some reason).

6. (Optional) As administrator start `taserverfirewall.py` in the `script` directory of this repository. This script will manage firewall rules to keep kicked players out and only allow logged in players on the game server.

7. Start the game server launcher by running the `start_game_server_launcher.py` script. This will launch a dedicated Tribes Ascend server. If starting the server fails, for instance because you specified the wrong directory in `data/gameserverlauncher.ini`, then it will keep on trying to start the server every 5 seconds. In that case use ctrl-C to shut it down and fix what's wrong.

8. Start your Tribes Ascend client using the shortcut you created earlier.

9. You can log on with any credentials. They are not checked (yet).

10. There should be one server in the server list. Connect to that and you will be connecting to your own dedicated server.

## Limitations

This is very much a work in progress and even basic functionality may not work correctly yet. This will come over time.
