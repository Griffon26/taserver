# Running taserver on Linux

## Ports
To make the server available publicly, you will have to open the following ports in your firewall or security group.

  -   7777/UDP
  -   7777/TCP
  -   7778/UDP
  -   7778/TCP
  -   9002/UDP

If the game server is running behind a router, you'll need to forward the above ports as well.

# Option 1: Docker

The simplest way to get a game server running on linux is to use the pre-built taserver-docker image.
See 
[chickenbellyfin/taserver on Docker Hub](https://hub.docker.com/r/chickenbellyfin/taserver) for full details.

Install docker and then run:
```
docker run \
  --name "taserver" -d --cap-add NET_ADMIN \
  -v "$(pwd)/gamesettings:/gamesettings" -p "9002:9002/tcp" \
  -p "7777:7777/tcp" -p "7777:7777/udp" \
  -p "7778:7778/tcp" -p "7778:7778/udp" \
  chickenbellyfin/taserver
```


# Option 2: Manual Setup

These instructions are if you would like to install and run taserver directly without using docker. The steps are specific to debian/ubuntu but it should be possible to use a different distribution as well.

## Install wine, python and other dependencies
Wine is used to run windows programs (Tribes Ascend) on linux. Python is required to run taserver. This step may take a long time.
```
$ sudo dpkg --add-architecture i386
$ sudo apt-get update
$ sudo apt-get install -y wine winetricks python3 python3-pip unzip
$ WINEARCH=win32 winetricks -q vcrun2017 dotnet48
$ sudo pip install -r requirements.txt
```

## Headless only: install xvfb
You only need this step if you are on a machine without a display, such as a server

```
$ sudo apt-get install xvfb
$ Xvfb :1 &> xvfb.out & export DISPLAY=":1"
```


## Make a `tribes` directory to keep everything in
```
$ mkdir /home/$USER/tribes && cd /home/$USER/tribes
```

## Download Tribes_Ascend_Parting_Gifts.zip and extract it to /home/$USER/tribes/Tribes_Ascend_Parting_Gifts/
[Tribes_Ascend_Parting_Gifts.zip download link](https://drive.google.com/uc?id=1hsjXFWJ2yvBCPNAy8SxQ2hT3XLIPvsrE&export=download)

## Download the latest release of taserver

```
$ cd /home/$USER/tribes

# Check https://github.com/Griffon26/taserver/releases and replace the TAG with the newest version
$ TAG="v2.8.0"
$ wget -O taserver.zip https://github.com/Griffon26/taserver/archive/refs/tags/$TAG.zip
$ unzip -q taserver.zip
$ mv $(ls | grep taserver-*) taserver && rm taserver.zip
```

## Update taserver configuration for linux

### Edit `taserver/data/gameserverlauncher.ini` as follows:

Update `dir = /home/$USER/tribes/Tribes_Ascend_Parting_Gifts/Binaries/Win32` where `$USER` is your username

`gameserverlauncher.ini` should look like this
```
[loginserver]
host = ta.kfk4ever.com
port = 9001

[gameserver]
dir = /home/<user>/tribes/Tribes_Ascend_Parting_Gifts/Binaries/Win32
controller_dll = TAMods-Server.dll
controller_config = gamesettings/ootb/serverconfig.lua
injector_exe = InjectorStandalone.exe
```


## Download TAMods-Server and InjectorStandalone:

```
$ cd /home/$USER/tribes/taserver
$ python3 download_compatible_controller.py
$ python3 download_injector.py
```

## Launch firewall and game_server_launcher
Run these steps every time you want to start the server.

```
$ cd /home/$USER/tribes/taserver

# If you installed xvfb in the earlier previous step, run it in the background
$ pkill Xvfb
$ Xvfb :1 &> xvfb.out & export DISPLAY=":1"

# start firewall and game server launcher
$ sudo python3 start_taserver_firewall.py &> /dev/null &
$ python3 start_game_server_launcher.py
```


