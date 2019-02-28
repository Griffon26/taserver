### taserver v2.0.1

Bugs fixed:
* starting the game without TAMods after switching to GOTY mode would not allow joining OOTB servers
* the speed of thrust with rage incorrectly depended on the capper's speed
  (this fix requires the versions mentioned below)

Compatibility notes:
* Game servers must have TAMods-Server version 0.4.1 or higher
* Clients must have a TAMods version 1.001 or higher


### taserver v2.0.0

This version is the first one to support running both GOTY and OOTB games on the same login server.

Here is the complete list of changes in this release:
* one login server now supports both OOTB and GOTY game servers.
  The mode of a game server is set through the game_setting_mode setting in gameserverlauncher.ini.
* passworded servers are now supported through a setting in gameserverlauncher.ini
* user names are now case insensitive and guaranteed to contain only printable ASCII
  (excluding space and DEL)
* a new "authbot" is provided for automating the user registration procedure.
  It logs on to the HiRez server and provides authcodes to people through private chat

Bug fixes:
* player IDs in the account database no longer change when they use an authcode
* parse.py can now parse failed authentications as well
* improved error logging for configuration errors in the game server launcher

Compatibility notes:
* Game servers have to be updated to this release in order to work with this login server version
* Game servers must have a TAMods-Server version of at least 0.4.0.
  Simply run `download_compatible_controller.py` after updating to this release to get it.
* For playing in GOTY mode, clients will need an up-to-date TAMods version.
  OOTB does not require TAMods on the client side.


### taserver v1.0.1

Bugs fixed:
* a game server could not connect to the login server if it was running on a different 
  host
* players could not join game servers if their game client was running on the same machine 
  as the login server    
* votekick did not work

Other changes:
* more detailed votekick logging on the login server


### taserver v1.0.0 released

6 months ago I posted here to announce that I was working on a project to host our own
Tribes Ascend servers and make it possible to kick out the hackers.

_I am happy to announce that [version 1.0.0 has now been released!](https://github.com/Griffon26/taserver/releases/tag/v1.0.0)_

The main login server at ta.kfk4ever.com (18.197.240.229) is running this version in OOTB
mode and will be up 24/7. Feel free to 
[start running game servers in your own region](https://github.com/Griffon26/taserver#hosting-a-dedicated-server)
and having them connect to this login server.

I am hosting a European game server myself on an 
[AWS T3 Medium instance](https://aws.amazon.com/ec2/instance-types/t3/),
which seems to be powerful enough and costs around 69 USD per month. 

In order to play on this server all you have to do is to [create a shortcut to TribesAscend.exe
and modify its properties slightly](https://github.com/Griffon26/taserver#joining-games)
I hope that next time a hacker is ruining your game on the official servers, you will give
this server a go!

I will continue to work on this project to implement more functionality and welcome your
input on what you think is most important. You can find me on 
[the taserver discord](https://discord.gg/8enekHQ)

Griffon26


### Hosting our own Tribes Ascend servers to get rid of hackers


For a while now players using hacks have been joining Tribes: Ascend games to ruin the fun for the rest of us. Because HiRez is not taking any action I've decided to come up with a solution myself.

For the past few months I've been working on a reimplementation of the Tribes Ascend login server that would allow us to run Tribes Ascend servers on our own infrastructure, making it possible to kick (and ban) the unkickable cheaters.

This reimplementation is not finished yet, but I wanted to at least let you know that it is coming. Take a look at this video: https://www.youtube.com/watch?v=apGxn0s9Mv0

The most important issues that still need to be solved before I can start running a server for you guys are:
* find a way to get team and match statistics from the game server (required for team chat & map changes)
* hosting: what kind of hardware/connection is needed to run a full game server smoothly?

Other than those blocking issues there are of course plenty of other things that need to be implemented before the server is fully functional.

I invite anyone who wants to help out to contact me by mail, discord (Griffon26#8007) or steam, especially if you think you can help me with one of the above blocking issues (people with knowledge of hosting game servers or of UDK games). And come join the public discord channel https://discord.gg/8enekHQ

Stay tuned!

Griffon26