## How to decode the login server protocol

This document describes how to capture traffic between the login server and a Tribes Ascend
client and how to turn it into a readable format that you can use to discover the meaning
of the protocol. 

The structure of the protocol has already been reverse engineered, so I will not describe
that here. Take a look at the code of the parse.py script if you want to know more about that.

### Capture with wireshark

First capture the traffic between your client and the login server with 
[Wireshark](https://www.wireshark.org/). They communicate over TCP on port 9000.

![Wireshark start capture](/docs/images/wireshark_start_capture.png?raw=true)

### Export to C arrays

Then follow the TCP stream:

![Wireshark follow TCP stream](/docs/images/wireshark_follow_tcp_stream.png?raw=true)

In the window that pops up you can save the entire conversation to a file as C arrays, 
but be sure to wait for the packet counters on the left to stop counting up before pressing
save, otherwise you'll only have part of the data.

![Wireshark save as C arrays](/docs/images/wireshark_saveas_carrays.png?raw=true)

### Convert to readable text with parse.py

Now run parse.py on the saved file to convert it to something readable:

    scripts\parse.py capture.carrays
    
The output file in the example scenario above will be named `capture.carrays_parsed.txt` and 
will look similar to this:

    --------------------------------------------------------------------------
    00000000`  0  : enumfield 01BC enumblockarray length 2
    00000004`      0  : enumfield 049E 01040B61 (field 0x049E: version number)
    0000000A`      1  : enumfield 0489 0000000C
    00000010`  1  : enumfield 003A enumblockarray length 1
    00000014`      0  : enumfield 049E 01040B61 (field 0x049E: version number)
    0000001A`  seq 00000000 ack 00000000
        --------------------------------------------------------------------------
        00000000`  0  : enumfield 01BC enumblockarray length 3
        00000004`      0  : enumfield 049E 01040B61 (field 0x049E: version number)
        0000000A`      1  : enumfield 0489 0000000C
        00000010`      2  : enumfield 0319 00000000
        00000016`  1  : enumfield 0197 enumblockarray length 3 (field 0x0197: diamond sword score)
        0000001A`      0  : enumfield 0664 0000115B
        00000020`      1  : enumfield 03E3 2F 08 CA 46 CF F1 82 49 93 BA A9 81 A3 FA 1E 40 (salt)
        00000032`      2  : enumfield 03E0 00000000
        00000038`  seq 00000000 ack 00000000
        --------------------------------------------------------------------------
        00000040`  0  : enumfield 003A enumblockarray length 3
        00000044`      0  : enumfield 049E 01040B61 (field 0x049E: version number)
        0000004A`      1  : enumfield 03E3 2F 08 CA 46 CF F1 82 49 93 BA A9 81 A3 FA 1E 40 (salt)
        0000005C`      2  : enumfield 0434 0B 54 DF 6B 2C 27 40 01
        00000066`  seq 00000001 ack 00000000
    --------------------------------------------------------------------------
    00000022`  0  : enumfield 003A enumblockarray length 11
    00000026`      0  : enumfield 0056 90 bytes containing authentication data based on your password
    00000086`      1  : enumfield 0494 "Griffon26" (field 0x0494: login name)
    00000093`      2  : enumfield 0671 00002841
    00000099`      3  : enumfield 0672 00000001
    0000009F`      4  : enumfield 0673 01
    000000A2`      5  : enumfield 0677 4358EEC3
    000000A8`      6  : enumfield 0676 00007FEF
    000000AE`      7  : enumfield 0674 00001002
    000000B4`      8  : enumfield 0675 0000679A
    000000BA`      9  : enumfield 0434 00 00 00 00 00 00 00 00
    000000C4`      10 : enumfield 049E 01040B61 (field 0x049E: version number)
    000000CA`  seq 00000000 ack 00000000
        --------------------------------------------------------------------------

### Extending parse.py

When you figure out the meaning of fields or values, add them to 
`scripts\known_field_data\enumfields.csv` and `scripts\known_field_data\fieldvalues.csv`
and the next time you run `parse.py` it will annotate the fields with your added 
descriptions.

### Troubleshooting

Sometimes the file saved by Wireshark contains improperly terminated C arrays. When
that happens use a text editor to delete them and run `parse.py` again.
