# Getting verified

To get rid of the "unvrf-" prefix to your name you need to get registered.
This document explains why this mechanism exists, how you register and how
a login server administrator generates authentication codes.

## Why this mechanism

Because the Hirez account database cannot be accessed from the custom login
server, the login server will have to maintain its own account database.
However, I wanted to allow someone who has used a certain account name on Hirez 
servers to be able to claim this same account name on the custom login server.
Also I did not want anyone else to be able to pose as this person. 

The only way I can make sure that I'm talking to a certain person is by
talking to them through private chat on the Hirez servers.

So the idea is that I give them an authentication code through private chat 
that they can then use on the custom login server to claim their account name.

Of course anyone running their own login server is free to use a different
approach to generating and distributing authentication codes.

## How to register

Below are two sets of instructions. One is for Griffon26's login server, the other
for any other login server. Most people should follow the first set of instructions,
because that server is where most game servers are listed. 

### For Griffon26's login server

Getting registered for the login server run by Griffon26 is an automated process:

1. First log in to the Hirez servers
1. Join a game server
1. Open the Chat Console. (This might not have a keybinding, add one through `Settings > Keybindings > Interface`). Note: This console is different to the Unreal Console (~)
1. Send a private chat message to `@taserverbot` with only the word `authcode` in it:

    `@taserverbot authcode`

1. If you get an error saying the player taserverbot is not online, message Griffon26 in Discord
1. Now log in to Griffon26's login server ("the community servers") with the in-game
   name you have on the Hirez server and a password of your choosing. Note that your
   in-game name could differ from your account name on Hirez servers. On the community
   servers your in-game name will be your account name.
1. After logging in go to the "Store" menu and select "Redeem promotion"
1. Fill in the authentication code and press OK
1. If you don't get an error message, registration was successful.
1. Restart Tribes Ascend and log in to Griffon26's server again to remove the "unvrf-" prefix.

### For any other login server

1. Ask the owner of the login server how to get an authentication code

2. The owner will either ask you for your desired account name or will provide
   it to you. He will also provide you with an authentication code. 

3. Once you have the authentication code, log on to the custom login server
   with the aforementioned account name and a password of your choosing

4. After logging in go to the "Store" menu and select "Redeem promotion"

5. Fill in the authentication code and press OK

6. If you don't get an error message, registration was successful.

7. Restart Tribes Ascend and log in to that login server again to remove the "unvrf-" prefix.
   
## How to generate authentication codes

Generating an authentication code is simple. Execute the following on the
machine that is running the login server:
 
    getauthcode.py <accountname>
 
This will put an authentication code in the account database for the specified
account name. When players register they choose their password. To change it
they will need another authentication code and go through registration again.
