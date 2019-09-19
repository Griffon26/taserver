# Creating a shortcut from a steam installation

* If you still have the shortcut properties dialog open, then close it by pressing `Cancel` 

  ![steam shortcut](../images/tashortcut_steam.png?raw=true)

* right-click on the steam icon in the system tray and select `Library`

  ![open steam library](../images/open_steam_library.gif?raw=true)

* in the list of games on the left find `Tribes: Ascend`, right-click on it and select `Properties`

  ![tribes ascend steam properties](../images/tribes_ascend_steam_properties.png?raw=true)

* in the dialog that opens go to the `Local Files` tab and click on the `BROWSE LOCAL FILES...` button

  ![browse local files](../images/browse_local_files.gif?raw=true)

* in the Explorer window that opens, double-click on the `Binaries` folder
* then double-click on the `Win32` folder
* find `TribesAscend.exe` in the list, right-click on it and choose `Send to`, followed by `Desktop`

  ![exe send to desktop](../images/exe_send_to_desktop.gif?raw=true)

* find the newly created shortcut on your desktop, probably named `TribesAscend.exe - Shortcut`, right-click on it and select `Properties`
* in the Dialog that opens, go to the end of the `Target` field and type a space followed by `-hostx=18.197.240.229`

  ![add hostx to target](../images/add_hostx_to_target.gif?raw=true)

* click `OK` to close the dialog
* you have now created a shortcut that you can use to start Tribes Ascend for playing on the community hosted servers
* after starting the game you can log in with any name and password, but be aware that 
  on the community servers **the login name you choose will also be your in-game name**.
  You can log in under a different name at any time though.

Possible next steps:
* [Getting verified](getting_verified.md)
* [Joining a GOTY server](joining_goty_servers.md)
