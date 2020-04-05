## Installing Tribes Ascend and prerequisites

If you want to run Tribes Ascend you may find that your system does not have 
all the packages that it requires.

For running Tribes Ascend you will need:

1. [Tribes Ascend Parting gifts version](#Tribes-Ascend-Parting-gifts-version)
2. [DirectX End-User Runtimes (June 2010)](#DirectX-End-User-Runtimes-June-2010)
3. [Visual C++ Redistributable for Visual Studio 2015 (x86 version)](#Visual-C++-Redistributable-for-Visual-Studio-2015-x86-version)

### Tribes Ascend Parting gifts version

The zip file containing the Tribes Ascend Parting gifts version can no longer be downloaded from Hirez.
The game [is still available through steam](https://store.steampowered.com/app/17080/Tribes_Ascend/),
but in case you cannot or do not want to install steam you can get the zip file using
[this direct download link](https://drive.google.com/uc?id=1hsjXFWJ2yvBCPNAy8SxQ2hT3XLIPvsrE&export=download).

You can check if your download matches the zip file originally published by Hirez by
calculating its hash with the following command (don't forget the SHA256 at the end):

    certutil -hashfile Tribes_Ascend_Parting_Gifts.zip SHA256

That should give you the following code:
   
    e0b1302db701986383a4dabda60e834313afc0e3c1322b5f80d443791811e046

If the code you get is different, this means that someone tampered with the contents
of the file and you should download a safe copy from another location. 

Once you have determined that the file has not been tampered with, extract it to a directory of your choice.

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
