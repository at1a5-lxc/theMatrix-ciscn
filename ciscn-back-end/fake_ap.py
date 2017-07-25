#! /usr/bin/env python
#-*- coding:utf8 -*-

import os
import threading
import signal
import time
import sys
import re
import pdb

def step1():
    os.system('ifconfig wlan1 down')
    os.system('iwconfig wlan1 mode monitor')
    os.system('ifconfig wlan1 up')
    os.system('airmon-ng start wlan1')
    os.system('airbase-ng -e qyh_test -c 6 wlan1')

def step2():
    os.system('ifconfig at0 up')
    os.system('ifconfig at0 10.0.0.1 netmask 255.255.255.0')
    os.system('route add -net 10.0.0.0 netmask 255.255.255.0 gw 10.0.0.1')
    
    os.system('echo 1 > /proc/sys/net/ipv4/ip_forward')
    
    os.system('dhcpd -cf /etc/dhcp/dhcpd.conf -pf /var/run/dhcpd.pid at0')
    os.system('# service isc-dhcp-server start')
    
    os.system('iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE')
    os.system('iptables -A FORWARD -i wlan1 -o eth0 -j ACCEPT')
    os.system('iptables -A FORWARD -p tcp --syn -s 10.0.0.0/24 -j TCPMSS --set-mss 1356')

# after ctrl+c
def quit(signum, frame):
    os.system('ifconfig wlan1 down')
    os.system('iwconfig wlan1 mode managed')
    os.system('ifconfig wlan1 up')

    s = os.popen('ps -aux | grep "/etc/dhcp/dhcpd.conf -pf /var/run/dhcpd.pid at0"')
    # pdb.set_trace()
    result = s.read()
    p = re.compile(r'\d+')
    pid = p.findall(result)[0]
    os.system('kill ' + pid)
    print '\nstop......\n'
    sys.exit()


if __name__ == '__main__':
    try:
        signal.signal(signal.SIGINT, quit)
        signal.signal(signal.SIGTERM, quit)
        
        a = threading.Thread(target = step1)
        b = threading.Thread(target = step2)

        a.setDaemon(True)
        a.start()
        time.sleep(20)

        b.setDaemon(True)
        b.start()
        
        while True:
            pass

    except Exception, exc:
        print exc
