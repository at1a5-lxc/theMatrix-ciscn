#encoding=utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf8")
import sqlite3
import time
import os
import os.path
rootdir = "d:\web"                                   # 指明被遍历的文件夹

def treeFileSystem(rootdir):
    retTumple=[]
    for parent,dirnames,filenames in os.walk(rootdir):    #三个参数：分别返回1.父目录 2.所有文件夹名字（不含路径） 3.所有文件名字
        for dirname in  dirnames:                       #输出文件夹信息
            path=os.path.join(parent,dirname)  #获取当前目录下的文件夹信息
            retTumple.append(path)
        for filename in filenames: 
            path=os.path.join(parent,filename) #获取当前目录下的文件信息
            retTumple.append(path)
    return retTumple


print "Begin walking"
recordTime=time.time()
files=treeFileSystem("d:\\web")
durtion=time.time()-recordTime
print "File amount:",len(files)
print "Cost:{}s".format(durtion)





