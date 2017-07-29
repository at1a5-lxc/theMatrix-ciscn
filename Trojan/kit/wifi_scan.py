#coding=utf-8

import os
import sys
import subprocess
import time
import json
from scapy.all import *
import csv


RSN = 48    #管理帧信息元素（Dot11Elt)ID48是RSN信息
WPA = 221   #管理帧信息元素ID221是WPA信息
Dot11i = {0:'GroupCipher',
          1:'WEP-40',
          2:'TKIP',
          4:'CCMP',
          5:'WEP-104'
          } #RSN信息的第6字节
WPA_Auth = {1:'802.11x/PMK',
            2:'PSK'
           } #RSN信息的第22字节
DN = open(os.devnull,'w')

def get_wlan_interfaces():
    '''
    返回当前PC上所有的无线网卡以及网卡所处的模式
    '''
    interfaces = {'monitor':[],'managed':[],'all':[]}
    proc = subprocess.Popen(['iwconfig'],stdout=subprocess.PIPE,stderr=DN)
    lines = proc.communicate()[0].split('\n')
    for line in lines:
        if line:
            if line[0] != ' ':
                iface = line.split(' ')[0]
                if 'Mode:Monitor' in line:
                    interfaces['monitor'].append(iface)
                if 'IEEE 802.11' in line:
                    interfaces['managed'].append(iface)
                interfaces['all'].append(iface)
    if len(interfaces['managed']) == 0:
        sys.exit('[!]没有无线网卡，请插入网卡')
    return interfaces

interfaces = get_wlan_interfaces()  #获取当前的无线网卡

def get_strongest_inface():
    '''
    通过iwlist dev scan命令，根据无线网卡可获取到的AP数量来判断哪个网卡的功率最强
    '''
    iface_APs = []
    #interfaces = get_wlan_interfaces()
    for iface in interfaces['managed']:
        count = 0
        if iface:
            proc = subprocess.Popen(['iwlist',iface,'scan'],stdout=subprocess.PIPE,stderr=DN)
            lines = proc.communicate()[0].split('\n')
            for line in lines:
                if line:
                    if '- Address:' in line:
                        count += 1
            iface_APs.append((count,iface))
    interface = max(iface_APs)[1]
    return interface

def start_monitor_mode():
    '''
    通过airmon-ng工具将无线网卡启动为监听状态
    '''
    if interfaces['monitor']:
        print '[*]监听网卡为：%s' % interfaces['monitor'][0]
        return interfaces['monitor'][0]
    interface = get_strongest_inface()
    print '[*]网卡%s开启监听模式...' % interface
    try:
        os.system('/usr/sbin/airmon-ng start %s' % interface)
        moni_inface = get_wlan_interfaces()['monitor']
        print '[*]监听网卡为：%s' % moni_inface[0]
        return moni_inface
    except:
        sys.exit('[!]无法开启监听模式')

def scan(moni_inface):
    airodump = subprocess.Popen(['airodump-ng', moni_inface,\
            '--write', 'wifi_scaned', '--output-format', 'csv'])
    time.sleep(10)
    airodump.kill()

    # find the latest version
    i = 1
    while os.path.isfile("wifi_scaned-0%d.csv"%i):
        i += 1

    cnt = -2
    stations = {}
    for row in csv.reader(open("wifi_scaned-0%d.csv"%(i-1))):
        if row and cnt >= 0:
            channel = row[3]
            Ciper = row[6]
            Authentication = row[7]
            Power = row[8]
            ESSID = row[13]
            stations[cnt] = [channel, Ciper, Authentication, Power, ESSID]
            cnt += 1
        if cnt < 0:
            cnt += 1
        if cnt > 0 and not row:
            break
    return json.dumps(stations)


def main():
    moni_inface = start_monitor_mode()
    print scan(moni_inface)

if __name__ == '__main__':
    main()
