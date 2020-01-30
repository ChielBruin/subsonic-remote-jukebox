import http.server, http.client
import socketserver
        
import re
import time
import traceback

from jukebox import Credentials


class RelayServer (http.server.BaseHTTPRequestHandler):
    @classmethod
    def init(cls, server_target, jukebox):
        cls.target = server_target
        cls.jukebox = jukebox

    def do_GET(self):
        self._handle_request()
        
    def do_POST(self):
        self._handle_request()
   
    def serve_404(self):
        self.send_response(404)
        self.end_headers()

    def send_jukebox_status(self, type):
        status = self.jukebox.get_status()
        
        if type is None or type == 'xml':
            response = status.to_xml()
        else:
            response = status.to_json()

        self.send_response(200)
        self.send_header('content-type', 'text/xml')
        self.end_headers()
        
        self.wfile.write(response)
       
    def _handle_stream(self):
        conn = http.client.HTTPConnection(self.target)
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

    def _parse_args(self, match):
        args = {}
        for (key, val) in [
            re.match(r'([\w\d]+)=([\w\d:\.]+)$', x).group(1,2) 
            for x in match.group(2).split('&')
        ]:
            if key in args:
                if isinstance(args[key], list):
                    args[key].append(val)
                else:
                    args[key] = [args[key], val]
            else:
                args[key] = val
        return args

    def _handle_relay(self):
        conn = http.client.HTTPConnection(self.target)
        conn.request('GET', self.path)
        res = conn.getresponse()                       
    
        self.send_response(res.status)
        self.send_header('content-type', res.getheader('content-type'))
        self.end_headers()
    
        self.wfile.write(res.read())

    def _handle_request(self):
        self.protocol_version = 'HTTP/1.1'
        match = re.match(r'/rest/([\w]+)(?:\.view)?\?([\w\d=&:\.]+)(?:#.*)?$', self.path)

        if match:
            group = match.group(1)
            if group == 'stream':
                self._handle_stream()
            
            elif group.startswith('jukeboxControl'):
                args = self._parse_args(match)
                credentials = Credentials(args)
            
                self._handle_jukebox_action(credentials, args)
                self.send_jukebox_status(args['f'] if 'f' in args else None)

            else:            
                self._handle_relay()
        else:
            self.serve_404()

    @classmethod
    def start(cls, port):
        try:
            with socketserver.TCPServer(('', port), RelayServer) as httpd:
                print('Serving at port %d' % port)
                httpd.serve_forever()
        except OSError as ex:
            if ex.errno == 98:
                print('Address already in use, trying again in 2 seconds')
                time.sleep(2)
                cls.start(port)
            else:
                raise ex

    def _handle_jukebox_action(self, credentials, args):
        if 'action' not in args:
            self.serve_missing_param(args)
        
        action = args['action']
        if action == 'get':
            print(args)
        elif action == 'status':
            pass # Status is always returned
        elif action == 'set':
            self.jukebox.set(id=args['id'] if 'id' in args else [], credentials=credentials)
        elif action == 'start':
            self.jukebox.play()
        elif action == 'stop':
            self.jukebox.pause()
        elif action == 'skip':
            self.jukebox.play(int(args['index']))
            if 'offset' in args:
                self.jukebox.set_position(int(args['offset']))
        elif action == 'add':
            self.jukebox.add(id=args['id'], credentials=credentials)
        elif action == 'clear':
            print(args)
        elif action == 'remove':
            print(args)
        elif action == 'shuffle':
            print(args)
        elif action == 'setGain':
            self.jukebox.set_volume(float(args['gain']))
        else:
            self.serve_missing_param(args)
        
    def serve_missing_params(self, args):     
        self.send_response(200)
        
        if 'f' not in args or args['f'] == 'xml':
            self.send_header('content-type', 'application/json; charset=UTF-8')
            response = b'<subsonic-response status="failed" version="1.16.1"> <error code="10" message="Required parameter is missing."/> </subsonic-response>'
        else:
            self.send_header('content-type', 'text/xml')
            response = b'''{
               "subsonic-response" : {
                     "status" : "failed",
                     "version" : "1.16.1",
                     "error" : {
                         "code" : 10,
                         "message" : "Required parameter is missing."
                     }
                }
            }'''
    
        self.end_headers()
        self.wfile.write(response)
        
