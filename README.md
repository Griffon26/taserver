# taserver
A replacement implementation of the Tribes Ascend login server

# IMPORTANT NOTICE: using this might get you banned! #
Although I have run this on my own machine with an internet connection and I have been able to log on to my real account afterwards, I can't guarantee that you won't get banned if you modify this code and connect to it.

## How to use it
If you do decide to try it out, here's how.

1. Create a shortcut to TribesAscend.exe with the following command line for starting a dedicated server:

    ```
    TribesAscend.exe server TrCtf-Katabatic
    ```
  
2. Create another shortcut to TribesAscend.exe with the following command line for starting a client that will connect to the login server running on your own machine:

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

3. Start the login server by running the main.py script in the server directory of this repository (preferably from a command window so you can read the errors if it exits for some reason).

4. Start both the dedicated server and the client using the shortcuts you created

5. You can log on with any credentials. They are not checked (yet).

6. There should be only one server in the server list. When you connect to that you will be connecting to your own dedicated server.

## Limitations

This is very much a work in progress and even basic functionality (such as correct player names or chat) does not work correctly yet. This will come over time.
