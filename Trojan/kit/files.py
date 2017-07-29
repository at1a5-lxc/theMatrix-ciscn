#encoding=utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf8")
import sqlite3
import time
import os
import os.path
import json
import threading

databaseMutex=threading.Lock() #如果有读请求 则停止更新数据库操作

def pwd():#返回当前路径
    return os.getcwd()

def cd(path):#进入到一个路径
    os.chdir(path)

def ls(path="."):#获取当前路径下的文件列表
    return filesView(path)

def filesView(dir_):#获取指定文件目录下的文件列表
    i = 0
    filesList = {}
    for line in os.listdir(dir_):
        try:
            sizes=os.path.getsize(dir_+"\\"+line)
            name=line.decode('gbk')
            if os.path.isdir(dir_+"\\"+line):
                filesList[i] = {    
                                    'name' : name, 
                                    'isDirectory' : 'true',
                                    'size' : sizes ,
                                    'path' : dir_
                                }
            else:
                filesList[i] = {    
                                    'name' : name, 
                                    'isDirectory' : 'false',
                                    'size' : sizes ,
                                    'path' :dir_
                                }
            i += 1
        except Exception as e:
            print "debug",e
    #return json.dumps(filesList)  #debug 这里修改了
    return filesList

def treeFileSystem(rootdir):
    global databaseMutex
    print "open dir.db"
    dirDB = sqlite3.connect('dir.db')
    try:
        dirDB.execute('''CREATE TABLE FILES
           (ID INTEGER PRIMARY KEY  AUTOINCREMENT,
            PATH     TEXT(200)    NOT NULL,
            NAME     TEXT(50)     NOT NULL);''')
    except Exception, exc:
        print exc
        print "Set NotExit False"
    else:
        print "Table created successfully"
        cnt = 0
        for parent,dirnames,filenames in os.walk(rootdir): #三个参数：分别返回1.父目录 2.所有文件夹名字（不含路径） 3.所有文件名字
            for dirname in  dirnames:                       #输出文件夹信息
                databaseMutex.acquire() #获取数据库的锁
                path=os.path.join(parent,dirname)  #获取当前目录下的文件夹信息
                # print path
                dirDB.execute('''INSERT INTO FILES (PATH, NAME) 
                VALUES ("%s", "%s");''' %(path.decode('gbk'), dirname.decode('gbk')))
                cnt += 1
                if(cnt%200==0):
                    dirDB.commit()
                if(cnt%1000==0):print cnt
                databaseMutex.release() #
                    #time.sleep(0.01)#release datacase lock
            for filename in filenames: 
                databaseMutex.acquire()
                path=os.path.join(parent,filename) #获取当前目录下的文件信息
                # print path
                dirDB.execute('''INSERT INTO FILES (PATH, NAME) 
                VALUES ("%s", "%s");''' %(path.decode('gbk'), filename.decode('gbk')))
                cnt += 1
                if(cnt%200==0):
                    dirDB.commit()
                if(cnt%1000==0):print cnt
                databaseMutex.release()
                    #time.sleep(0.01)#release database lock
        dirDB.commit()
        dirDB.close()

'''
sizes=os.path.getsize(dir_+"\\"+line)
            name=line.decode('gbk')
            if os.path.isdir(dir_+"\\"+line):
'''


def searchFile(filename,limit=100):
    global databaseMutex
    try:
        databaseMutex.acquire() #获取数据库锁
        result=()
        dbPath='dir.db'
        if(os.path.exists(dbPath)==False):
            print 'Database not created!'
            return {}
        dirDB  = sqlite3.connect(dbPath)
        cursor = dirDB.cursor()
        cursor.execute("select * from FILES where NAME like '%{}%' and PATH not like '%$RECYCLE%'  limit {}".format(filename,limit))
        tuple_result = cursor.fetchall()
        result={}
        for index,items in enumerate(tuple_result):
            #print "debug:pathname=[{}]".format(items[1])
            if(os.path.isdir(items[1])):
                isDirectory="true"
            else:
                isDirectory="false"
            sizes=os.path.getsize(items[1])
            path,name=os.path.split(items[1])
            result[index]={'path':path,'name':name,'size':sizes,'isDirectory':isDirectory}
        #result=json.dumps(result)
    except Exception as e:
        print e
    finally:
        databaseMutex.release()
        return result

def createFileDatabaseThread(path="D:\\"):#创建后台文件系统数据库线程
    fileSystemThread = threading.Thread(target=treeFileSystem,args=(path,))
    fileSystemThread.setDaemon(True)
    fileSystemThread.start()
    print "fileSystemThread started"

if __name__ == "__main__":
    import pic
    print pic.CameraShot(uploadUrl="http://127.0.0.1:8091/upload")
    time.sleep(0.1)
    print "Done"
