#encoding=utf-8
import urllib2
import time
import os
import os.path
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
def uploadFileToServer(filepath,serverUrl="http://127.0.0.1:8071/upload"):
    filepath=filepath.decode("utf-8")#这里是新加入的解码语句 谨防出错
    boundary = '----------%s' % hex(int(time.time() * 1000))
    data = []
    data.append('--%s' % boundary)
    if( os.path.exists(filepath) ):
        print "Filepath:{}".format(filepath)
        fr=open(filepath,'rb')
        filename=os.path.split(filepath)[1]
        data.append('Content-Disposition: form-data; name="file"; filename="{}"'.format(filename))
        print data
        data.append('Content-Type: %s\r\n' % 'application/octet-stream')
        data.append(fr.read())
        fr.close()
        data.append('--%s--\r\n' % boundary)
        http_url=serverUrl
        http_body='\r\n'.join(data)
        try:
            #buld http request
            req=urllib2.Request(http_url, data=http_body)
            #header
            req.add_header('Content-Type', 'multipart/form-data; boundary=%s' % boundary)
            req.add_header('User-Agent','Mozilla/5.0')
            #post data to server
            resp = urllib2.urlopen(req, timeout=5)
            #get response
            qrcont=resp.read()
            print "uploadFile.py: success upload {}".format(filepath)
            return 'success:success'
        except Exception,e:
            print 'http error',e
            return 'fail:http error'
    else:
        print "File doesn't exists!"
        return "fail:file doesn't exists"

if __name__ == '__main__':
    print uploadFileToServer('D:\\work\\hack\\matrix\\kit\\screenshot.jpg',"http://127.0.0.1:8071/upload")
    print "Done"

