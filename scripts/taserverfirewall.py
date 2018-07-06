#!/usr/bin/env python3

import argparse
import gevent
import gevent.queue
from gevent.server import StreamServer
import gevent.subprocess as sp
import re

whitelistfilename = 'firewallwhitelist.txt'

def readiplist(filename):
    iplist = set()
    
    with open(filename, 'rt') as f:
        for line in f:
            line = line.strip()

            match = re.match('\d+\.\d+\.\d+\.\d+', line)
            if match:
                try:
                    ipparts = tuple(int(x) for x in line.split('.'))
                    if not all(0 <= p <= 255 for p in ipparts):
                        raise RuntimeError('Not a valid IP')

                    iplist.add(ipparts)
                
                except RuntimeError:
                    pass

    return iplist

def writeiplist(filename, iplist):
    with open(filename, 'wt') as f:
        for ip in sorted(iplist):
            f.write('%d.%d.%d.%d\n' % ip)

def removeallrules():
    args = [
        'c:\\windows\\system32\\Netsh.exe',
        'advfirewall',
        'firewall',
        'delete',
        'rule',
        'name="TAserverfirewall"'
    ]
    # Don't check for failure here, because it is expected to
    # fail if there are no left-over rules from a previous run.
    sp.call(args)

def removewhitelistrule(ip):
    args = [
        'c:\\windows\\system32\\Netsh.exe',
        'advfirewall',
        'firewall',
        'delete',
        'rule',
        'name="TAserverfirewall"',
        'protocol=udp',
        'dir=in',
        'profile=Private',
        'localport=7777',
        'remoteip=%d.%d.%d.%d' % ip
    ]
    try:
        sp.check_call(args)
    except sp.CalledProcessError as e:
        print('Failed to remove rule from firewall.')

def addwhitelistrule(ip):
    args = [
        'c:\\windows\\system32\\Netsh.exe',
        'advfirewall',
        'firewall',
        'add',
        'rule',
        'name="TAserverfirewall"',
        'protocol=udp',
        'dir=in',
        'enable=yes',
        'profile=Private',
        'localport=7777',
        'action=allow',
        'remoteip=%d.%d.%d.%d' % ip
    ]
    try:
        sp.check_call(args)
    except sp.CalledProcessError as e:
        print('Failed to add rule to firewall.')

def handleserver(serverqueue):
    try:
        iplist = readiplist(whitelistfilename)
        print('Loaded IP list from %s' % whitelistfilename)
    except FileNotFoundError:
        print('File not found. Starting with empty IP list')
        iplist = set()

    # Default is to block, so for a whitelist we only need to add allow rules
    removeallrules()
    for ip in iplist:
        addwhitelistrule(ip)
    
    while True:
        action, ip = serverqueue.get()

        if action == 'add':
            if ip not in iplist:
                print('add firewall rule for', ip)
                iplist.add(ip)
                addwhitelistrule(ip)
        else:
            if ip in iplist:
                print('remove firewall rule for', ip)
                iplist.remove(ip)
                removewhitelistrule(ip)

        writeiplist(whitelistfilename, iplist)
       
def main(args):
    serverqueue = gevent.queue.Queue()
    
    gevent.spawn(handleserver, serverqueue)

    def handleclient(socket, address):
        ipbytes = socket.recv(5)
        socket.close()
        if(len(ipbytes) == 5):
            serverqueue.put( ('add' if ipbytes[0] == ord('a') else 'remove',
                              (ipbytes[1], ipbytes[2], ipbytes[3], ipbytes[4])) )

    server = StreamServer(('127.0.0.1', 9801), handleclient)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        removeallrules()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main(args)

