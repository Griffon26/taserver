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
    print('Removing any previous TAserverfirewall rules')
    sp.call(args, stdout=sp.DEVNULL)

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
        'profile=any',
        'localport=7777',
        'remoteip=%d.%d.%d.%d' % ip
    ]
    try:
        sp.check_output(args, text = True)
    except sp.CalledProcessError as e:
        print('Failed to remove rule from firewall:\n%s' % e.output)

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
        'profile=any',
        'localport=7777',
        'action=allow',
        'remoteip=%d.%d.%d.%d' % ip
    ]
    try:
        sp.check_output(args, text = True)
    except sp.CalledProcessError as e:
        print('Failed to add rule to firewall:\n%s' % e.output)

def findtribesascendrules():
    args = [
        'c:\\windows\\system32\\Netsh.exe',
        'advfirewall',
        'firewall',
        'show',
        'rule',
        'name=all',
        'dir=in',
        'status=enabled',
        'verbose'
    ]
    try:
        output = sp.check_output(args, text = True)
    except sp.CalledProcessError as e:
        print('Failed to request firewall rules.')
        output = ''

    tarules = []
    for line in output.splitlines():
        if line.startswith('Rule Name:'):
            newrule = {}
        elif ':' in line:
            key, value = line.split(':', maxsplit=1)
            key = key.strip()
            value = value.strip()
            
            newrule[key] = value

            if key == 'Program' and value.lower().endswith('tribesascend.exe'):
                tarules.append(newrule)

    return tarules
            
def disablerulesforprogramname(programname):
    args = [
        'c:\\windows\\system32\\Netsh.exe',
        'advfirewall',
        'firewall',
        'set',
        'rule',
        'name=all',
        'dir=in',
        'program="%s"' % programname,
        'new',
        'enable=no'
    ]
    
    try:
        print('Disabling rule for %s' % programname)
        sp.check_output(args, text = True)
    except sp.CalledProcessError as e:
        print('Failed to remove firewall rules for program %s. Output:\n%s' %
              (programname, e.output))
    
def handleserver(serverqueue):
    try:
        iplist = readiplist(whitelistfilename)
        print('Loaded IP list from %s' % whitelistfilename)
    except FileNotFoundError:
        print('File not found. Starting with empty IP list')
        iplist = set()

    # First disable the rules that are created by Windows itself when you run tribesascend.exe
    tribesascendprograms = set(rule['Program'] for rule in findtribesascendrules())
    for program in tribesascendprograms:
        disablerulesforprogramname(program)
        
    # Default is to block, so for a whitelist we only need to add allow rules
    removeallrules()
    for ip in iplist:
        print('Adding rule to allow %d.%d.%d.%d' % ip)
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

