# -*- coding:utf-8 -*-
import os
import sys
import json
import time
import tornado.httpserver
import tornado.web
import tornado.ioloop
import thread
from tornado import websocket
import random
import uuid
import RPi.GPIO as GPIO  
import sys
import serial
reload(sys)
sys.setdefaultencoding('utf-8')
listenPort=8888
currentPressure=123
currentDepth=50
currentAngle=45
lastSpeedH=0
#mega=serial.Serial("/dev/ttyACM0",115200)



def dataTransfer():
    while True:
        try:
            dataToSend={}
            dataToSend['pressure']=123
            dataToSend['time']=time.time()
            msg=json.dumps(dataToSend)
            print "Send ",msg
            SocketHandler.send_to_all(msg)
            time.sleep(1)
        except:
            print "Error"
            time.sleep(2)


class SocketHandler(tornado.websocket.WebSocketHandler):
    clients = set()

    def check_origin(self, origin):  
        return True

    @staticmethod
    def send_to_all(message):
        for c in SocketHandler.clients:
            c.write_message(message)

    def open(self):
        SocketHandler.clients.add(self)
        print "new connection build"

    def on_close(self):
        SocketHandler.clients.remove(self)

    def on_message(self, message):
        global lastSpeedH
        print "Recv:",message
        data=json.loads(message)
        dataType=data['type']
        dataContent=data['content']


if __name__ == '__main__':
    listenPort=8888
    app = tornado.web.Application([
        ('/soc', SocketHandler)
    ],cookie_secret='abcd',
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    static_path=os.path.join(os.path.dirname(__file__), "templates"),
    )
    print "Running"
    thread.start_new_thread(dataTransfer,())
    app.listen(listenPort)
    tornado.ioloop.IOLoop.instance().start()
    mega.close()
