#!/usr/bin/env python3

import argparse
import gevent
import gevent.queue
from gevent.server import StreamServer
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

def handleserver(serverqueue):

    try:
        iplist = readiplist(whitelistfilename)
        print('Loaded IP list from %s' % whitelistfilename)
    except FileNotFoundError:
        print('File not found. Starting with empty IP list')
        iplist = set()

    # TODO: set up all the rules according to iplist
    
    while True:
        action, ip = serverqueue.get()

        if action == 'add':
            if ip not in iplist:
                # TODO: add a firewall rule
                print('add firewall rule for', ip)
                iplist.add(ip)
        else:
            if ip in iplist:
                # TODO: remove a firewall rule
                print('remove firewall rule for', ip)
                iplist.remove(ip)

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
    server.serve_forever()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main(args)

