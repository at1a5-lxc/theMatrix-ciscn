#encoding=utf-8
from VideoCapture import Device
from PIL import ImageGrab
import os
import uploadFile
import time
import logging

def CameraShot(uploadUrl="http://127.0.0.1:8071/upload"):
    print("Enter CameraShot func")
    cam = Device()
    imageNameWithoutPath=time.strftime("%Y%m%d%H%M%S", time.localtime())+"-camerashot.jpg"
    imageNameWithPath=time.strftime("D:\\"+"%Y%m%d%H%M%S", time.localtime())+"-camerashot.jpg"
    cam.saveSnapshot(imageNameWithPath)
    uploadFile.uploadFileToServer(imageNameWithPath,uploadUrl)
    return imageNameWithoutPath

def ScreenShot(uploadUrl="http://127.0.0.1:8071/upload"):
    snapshot = ImageGrab.grab()
    imageName=time.strftime("%Y%m%d%H%M%S", time.localtime())+"-screenshot.jpg"
    snapshot.save(imageName)# 20170728001651-screenshot.jpg
    uploadFile.uploadFileToServer(imageName,uploadUrl)#这里如果出错了 那么有可能是uploadFile的路径和pic的路径不一致了
    return imageName

if __name__ == "__main__":
    print CameraShot(uploadUrl="http://127.0.0.1:8091/upload")
    time.sleep(0.1)
    print "Done"