# Getting verified

Here is what you get by verifying your account:
* no one else can use your name
* no more "unvrf-" in front of your name
* loadouts and friends will be saved
* you can vote for the next map

This document explains why this mechanism exists, how to get verified and how
a login server administrator can generate authentication codes manually.

## Why this mechanism

I believe it would not be good for the community if anyone could just assume
any name regardless of anyone else using the same name. For this reason I 
want people to be able to claim a name for themselves.

Until recently this was only possible if you owned said name on the Hirez servers.
Unfortunately the Hirez servers are now down so often that I can no longer
rely on them for the verification mechanism.

The current verification mechanism relies on email instead. When requesting
verification your email address is associated with your account, making sure
that from then on only you can change the account password.

## How to get verified

Usually the administrator of the login server will be running a bot for
verification purposes, in which case getting verified is an automated process: 

1. Log on to the community servers with the name and password you would like
   to use.

2. Load a map by either joining a game server or starting one of the trainings

3. Open the Chat Console by pressing `esc` to open the menu and then pressing `t`.
   Note: This chat console is different to the Unreal Console (~)
   
4. Send a private chat message to `taserverbot` containing the word `authcode` 
   followed by your email address:

   ![asking for an authcode](../images/ask_for_authcode.gif?raw=true)
    
5. Wait for the verification mail to arrive and look up the authentication code
   it contains. Check your spam box if you cannot find the mail. If you do not
   receive any mail it may be because the account already exists and the specified
   email address does not match the email address for that account.
 
    Note: Authentication codes will remain active for 4 hours. After that you will
    have to request a new one.
    
6. in Tribes Ascend go to the "Store" menu and select "Redeem promotion"

7. Fill in the authentication code and press OK

8. You will get a message telling you if verification was successful.

9. Restart Tribes Ascend and log in again to remove the "unvrf-" prefix

## Changing the email address associated with your account

If you want to change the email address associated with your account, follow these steps:

1) Log in to your account on the custom login server 

2) Send a private message to `taserverbot` containing the word `setemail`
   followed by your email address.

## Getting verified if the server administrator is not using taserverbot

1. Ask the owner of the login server how to get an authentication code

2. The owner will ask you for your desired account name and email address,
   after which he will provide you with an authentication code. 

3. Once you have the authentication code, log on to the custom login server
   with the aforementioned account name and a password of your choosing

4. After logging in go to the "Store" menu and select "Redeem promotion"

5. Fill in the authentication code and press OK

6. You will get a message telling you if verification was successful.

7. Restart Tribes Ascend and log in to that login server again to remove the "unvrf-" prefix.
   
## How to generate authentication codes

Generating an authentication code is simple. Execute the following on the
machine that is running the login server:
 
    getauthcode.py <accountname> <email address>
 
This will put an authentication code in the account database for the specified
account name. When players register they choose their password. To change it
they will need another authentication code and go through registration again.
