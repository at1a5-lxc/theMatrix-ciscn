#encoding=utf-8
import os
import sys
import json
import time
import tornado.httpserver
import tornado.web
import tornado.ioloop
import md5
import thread
import threading
import logging
from tornado import websocket
import random
import uuid
import sqlite3
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class Index(tornado.web.RequestHandler):
    def get(self):
        global listenPort
        print "[+]Enter get index"
        self.render("index.html",ipAddress="localhost",lp=8080)

class FileDownloadHandler(tornado.web.RequestHandler):#文件下载处理类
    def get(self):
        filename="download/"+self.get_argument("filename") #"test.txt"
        if(os.path.exists(filename)==False):#判断该文件是否存在
            self.write("No such file")
            self.finish()
        else:
            self.set_header ('Content-Type', 'application/octet-stream')
            self.set_header ('Content-Disposition', 'attachment; filename='+filename)
            buf_size=4096#每次读取的文件缓存
            with open(filename, 'rb') as f:
                while True:
                    data = f.read(buf_size)
                    if not data:
                        break
                    self.write(data)
            self.finish()

class FileUploadHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('''
        <html>
          <head><title>Upload File</title></head>
          <body>
            <form action='upload' enctype="multipart/form-data" method='post'>
            <input type='file' name='file'/><br/>
            <input type='submit' value='submit'/>
            </form>
          </body>
        </html>
        ''')
    def post(self):
        upload_path=os.path.join(os.path.dirname(__file__),'upload')   #文件的暂存路径
        file_metas=self.request.files['file']  #提取表单中‘name’为‘file’的文件元数据
        for meta in file_metas:
            filename=meta['filename']
            filepath=os.path.join(upload_path,filename)
            with open(filepath,'wb') as up:#全部以二进制方式写入 这样更加安全
                up.write(meta['body'])
            self.write('finished!')

class SocketHandler(tornado.websocket.WebSocketHandler):#websocket句柄
    clients =set()

    @staticmethod
    def send_to_all(message):
        for c in SocketHandler.clients:
            c.write_message(message)
            logging.info("Send {} to {}".format(message,id(c)))

    def open(self):#一个新的websocket开启了
        SocketHandler.clients.add(self)
        logging.info("New connection from {}".format(id(self)))

    def on_close(self):#websocket断开连接
        SocketHandler.clients.remove(self)
        logging.info("{} detached".format(id(self)))

    def on_message(self, message):#websocket接收到客户端发送过来的数据
        logging.info("{} says:{}".format(id(self),message))

def intervalSendMsg():
    while True:
        SocketHandler.send_to_all("{}".format(time.ctime()))
        time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s [%(levelname)s]  %(message)s",
                    datefmt='%Y/%m/%d %H:%M:%S',
                    #filename='_server_.log',filemode='a'
                    )# debug info warning error cirtical
    app = tornado.web.Application([
        ('/', Index),
        ('/soc', SocketHandler),#用来处理websocket连接
        ('/download',FileDownloadHandler),#用来处理文件下载请求
        ('/upload',FileUploadHandler),#用来处理文件上传请求
        ],
        cookie_secret='abcd',
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
    )
    app.listen(8080)
    logging.info("Server is running...")
    threading.Thread(target=intervalSendMsg,args=()).start()
    tornado.ioloop.IOLoop.instance().start()
