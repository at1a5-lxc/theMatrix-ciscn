import urllib2
import time
import os
import os.path
def uploadFileToServer(filepath,serverUrl="http://223.3.113.114:8080/upload"):
    boundary = '----------%s' % hex(int(time.time() * 1000))
    data = []
    data.append('--%s' % boundary)
    #data.append('Content-Disposition: form-data; name="%s"\r\n' % 'testTag')
    #data.append('12345')
    #data.append('--%s' % boundary)
    if( os.path.exists(filepath) ):
        fr=open(filepath,'rb')
        data.append('Content-Disposition: form-data; name="file"; filename="%s"' % filepath)
        data.append('Content-Type: %s\r\n' % 'application/octet-stream')
        data.append(fr.read())
        fr.close()
        data.append('--%s--\r\n' % boundary)

        server_url='http://127.0.0.1:8080/upload'
        http_body='\r\n'.join(data)
        try:
            #buld http request
            req=urllib2.Request(server_url, data=http_body)
            #header
            req.add_header('Content-Type', 'multipart/form-data; boundary=%s' % boundary)
            req.add_header('User-Agent','Mozilla/5.0')
            #post data to server
            resp = urllib2.urlopen(req, timeout=5)
            #get response
            qrcont=resp.read()
            print qrcont
        except Exception,e:
            print 'http error'
    else:
        print "File doesn't exists!"

if __name__ == '__main__':
    uploadFileToServer("ciscn.zip")