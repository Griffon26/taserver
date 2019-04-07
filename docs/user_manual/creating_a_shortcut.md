# Creating a shortcut

This guide will show you step by step and with screenshots how to create a shortcut that you can 
use to launch Tribes Ascend and connect to the community hosted servers. You will only need to do
this once. The next time you want to play on community servers you can just double-click the already
created shortcut. 

Find the shortcut that you use to start Tribes Ascend.

Click it with the right mouse button and click on Properties.

Now check if the dialog that opens look more like the screenshot on the left or the one on the right

[![steam shortcut](../images/tashortcut_steam.png?raw=true)](#For_the_steam_version)
[![non-steam shortcut](../images/tashortcut_nonsteam.png?raw=true)](#For_the_non_steam_version)

Make your choice:
* [It looks like the one on the left](#For_the_steam_version)
* [It looks like the one on the right](#For_the_non_steam_version)

### For the steam version

* close the Properties dialog by pressing Cancel
* right-click on the steam icon in the system tray and select Library

![open steam library](../images/open_steam_library.gif?raw=true)

* in the list of games on the left find Tribes: Ascend, right-click on it and select Properties

![tribes ascend steam properties](../images/tribes_ascend_steam_properties.png?raw=true)

* in the dialog that opens go to the Local Files tab and click on the BROWSE LOCAL FILES... button

![browse local files](../images/browse_local_files.gif?raw=true)

* in the Explorer window that opens, double-click on the Binaries folder
* then double-click on the Win32 folder
* find TribesAscend.exe in the list, right-click on it and choose Send to, followed by Desktop

![send to desktop](../images/send_to_desktop.gif?raw=true)

* find the newly created shortcut on your desktop, probably named `TribesAscend.exe - Shortcut`, right-click on it and select Properties
* in the Dialog that opens, go to the end of the Target field, type a space followed by `-hostx=18.197.240.229`

![send to desktop](../images/add_hostx_to_target.gif?raw=true)

* click OK to close the dialog
* you have now created a shortcut that you can use to start TribesAscend for playing on the community hosted servers

### For the non-steam version

* close the Properties dialog by pressing Cancel
* right-click on the shortcut and choose Send to, followed by Desktop
* find the newly created shortcut on your desktop, probably with a name similar to the original shortcut, right-click on it and select Properties
* in the Dialog that opens, go to the end of the Target field, and replace the numbers after `-hostx=` with `18.197.240.229`
* optionally choose a different name for this shortcut by clicking on the `General` tab and editing the name field at the top
* click OK to close the dialog
* you have now created a shortcut that you can use to start TribesAscend for playing on the community hosted servers