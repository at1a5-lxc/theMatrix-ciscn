#encoding=utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf8")
import sqlite3
import time
import os
import os.path
import json

def filesView(dir):
    i = 0
    filesList = {}
    for line in os.listdir(dir):
        if os.path.isdir(line):
            filesList[i] = [line.decode('gbk'), False]
        else:
            filesList[i] = [line.decode('gbk'), True]
        i += 1
    return json.dumps(filesList)


def treeFileSystem(rootdir):
    print "open dir.db"
    dirDB = sqlite3.connect('dir.db')
    try:
        dirDB.execute('''CREATE TABLE FILES
           (ID INTEGER PRIMARY KEY  AUTOINCREMENT,
            PATH     TEXT(200)    NOT NULL,
            NAME     TEXT(50)     NOT NULL);''')
    except Exception, exc:
        print exc
    else:
        print "Table created successfully"

        cnt = 0
        for parent,dirnames,filenames in os.walk(rootdir): #三个参数：分别返回1.父目录 2.所有文件夹名字（不含路径） 3.所有文件名字
            for dirname in  dirnames:                       #输出文件夹信息
                path=os.path.join(parent,dirname)  #获取当前目录下的文件夹信息
                # print path
                dirDB.execute('''INSERT INTO FILES (PATH, NAME) 
                VALUES ("%s", "%s");''' %(path.decode('gbk'), dirname.decode('gbk')))
                cnt += 1

            for filename in filenames: 
                path=os.path.join(parent,filename) #获取当前目录下的文件信息
                # print path
                dirDB.execute('''INSERT INTO FILES (PATH, NAME) 
                VALUES ("%s", "%s");''' %(path.decode('gbk'), filename.decode('gbk')))
                cnt += 1
        dirDB.commit()
        dirDB.close()

def beginSearch(rootdir):
    print "Begin walking"
    recordTime=time.time()

    filesNum=treeFileSystem(rootdir)

    durtion=time.time()-recordTime

    print "File amount:", filesNum
    print "Cost:{}s".format(durtion)

if __name__ == "__main__":
    beginSearch("D:\\")
    # print filesView("D:\\")
