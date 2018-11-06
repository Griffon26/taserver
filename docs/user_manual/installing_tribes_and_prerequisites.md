## Installing Tribes Ascend and prerequisites

If you want to run a game server you may find yourself installing
the game on a clean system that does not have all the packages that 
it requires.

For running Tribes Ascend as a server you will need:

1. [Tribes Ascend Parting gifts version](#Tribes-Ascend-Parting-gifts-version)
2. [DirectX End-User Runtimes (June 2010)](#DirectX-End-User-Runtimes-June-2010)
3. [Visual C++ Redistributable for Visual Studio 2015 (x86 version)](#Visual-C++-Redistributable-for-Visual-Studio-2015-x86-version)

If you actually want to use the Tribes Ascend installation that you 
now have, follow the instructions in the [Hosting a dedicated server](../../README.md#Hosting a dedicated server)
section of the README accompanying this project.

### Tribes Ascend Parting gifts version

The zip file containing the Tribes Ascend Parting gifts version can be
[downloaded from hirez](http://lwcdn.hi-rezgame.net/media/iso/Tribes_Ascend_Parting_Gifts.zip).
Extract this to a directory of your choice.

### DirectX End-User Runtimes (June 2010)

The DirectX end-user runtimes come with the parting gifts release of Tribes.
They are located in the folder `Tribes_Ascend_Parting_Gifts\Binaries\Redist`.
Run the self-extracting archive `directx_Jun2010_redist.exe` and extract it
to any location.

Once that is done find `dxsetup.exe` among the extracted contents and run it.
This will install any missing DirectX files.

### Visual C++ Redistributable for Visual Studio 2015 (x86 version) 

Download the [Visual C++ Redistributable for Visual Studio 2015](https://www.microsoft.com/en-us/download/details.aspx?id=48145)
from Microsoft and install it. Be sure to choose the x86 version. 

