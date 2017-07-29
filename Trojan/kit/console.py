#-*- coding:utf8 -*-

import os
import threading
import signal
import time
import sys
import re
import pdb
from files import treeFileSystem, filesView
from pic import CameraShot, ScreenShot

# after ctrl+c
# def quit(signum, frame):

# def main():
    # get command
    # do something
    # return something

if __name__ == '__main__':
    try:
        signal.signal(signal.SIGINT, quit)
        signal.signal(signal.SIGTERM, quit)
        
        a = threading.Thread(target = treeFileSystem, args=("D:\\", ))
        a.setDaemon(True)
        a.start()

        currentPath = "D:\\"
        print filesView(currentPath)

        while(1):
            time.sleep(1)

    except Exception, exc:
        print exc
