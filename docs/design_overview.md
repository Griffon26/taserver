# Design overview

The taserver software consists of three parts that work together to provide
the full functionality of the Tribes Ascend login server. The following 
diagram shows where these parts are deployed.

The lines indicate communication channels between the various parts.
The arrow indicates in what direction the connection is initiated.

![PlantUML model](http://www.plantuml.com/plantuml/png/5Sqz3i8m343XdLF01MA9WO6f6yUeGkAsbX8xyazxVSBqXczuYtbMZzvk3-BIec9ekn_kmzu0cg-qan_n3KCjmexigKY7ZzAs2JzVu7dIYGezcyzKAGOLZNPUvPn4UANnFop8TVO7)

### taserver login server

When a player logs in his client will connect to the login server.
Here's a list of responsibilities for the login server:
 
* player authentication
* providing chat functionality (but not VGS)
* managing the votekick process
* providing the dedicated server with player loadout information
* triggering a map change when the match has ended

### taserver game launcher

The game launcher was made to:

* start the dedicated server
* inject the taserver game controller into the dedicated server 
* register it with the login server so it shows up in the server list
* allow the game controller to request player loadout information
* forward match information from game controller to login server

### taserver game controller

On Hirez' infrastructure the dedicated server communicates with
the login server for validation of player loadouts. Because the
dedicated server as we have it does not appear to support this,
we inject the game controller into the server to take care of
loadout validation.

This also makes it the ideal place for reporting on other 
match information that the login server requires.

In short the game controller must:

* transfer player loadout information from the taserver game 
  launcher to the dedicated server when the dedicated server
  needs to validate a loadout
* report remaining match time to the game launcher
* report team selection for each player to the game launcher
