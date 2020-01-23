import http.server, http.client
import socketserver
        
import re

PORT = 4040
SUBSONIC_TARGET = '192.168.1.71:4040'
HARD_REDIRECT = False


class SubsonicRelay (http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle_request()
        
    def do_POST(self):
        self._handle_request()
    
    def send_jukebox_status(self):
        response_format = b'<subsonic-response status="ok" version="1.7.0"> <jukeboxStatus currentIndex="%d" playing="%s" gain="%1.2f" position="%d"/> </subsonic-status>'
        response = response_format % (7, b'true', 0.9, 67)
        
        self.send_response(200)
        self.send_header('content-type', 'text/xml')
        self.end_headers()
        
        self.wfile.write(response)
        
    def _handle_request(self):
        self.protocol_version = 'HTTP/1.1'
        match = re.match(r'/rest/([\w]+)', self.path)

        if match:
            group = match.group(1)
            if group == 'stream':
                conn = http.client.HTTPConnection(SUBSONIC_TARGET)
                conn.request('GET', self.path)
                res = conn.getresponse()                       
            
                self.send_response(res.status)
                self.send_header('content-type', res.getheader('content-type'))
                self.end_headers()
            
                chunk = res.read(1024)
                while chunk:
                    self.wfile.write(chunk)
                    chunk = res.read(1024)
                return
            
            elif group == 'jukeboxControl':
                print('jukebox!!')
                print(self.path)
                self.play()
                self.send_jukebox_status()
            else:            
                conn = http.client.HTTPConnection(SUBSONIC_TARGET)
                conn.request('GET', self.path)
                res = conn.getresponse()                       
            
                self.send_response(res.status)
                self.send_header('content-type', res.getheader('content-type'))
                self.end_headers()
            
                self.wfile.write(res.read())
        else:
            print('else: %s' % self.path)
            pass

def main():
    with socketserver.TCPServer(('', PORT), SubsonicRelay) as httpd:
        print('Serving at port %d'%PORT)
        httpd.serve_forever()

if __name__ == '__main__':
    main()

