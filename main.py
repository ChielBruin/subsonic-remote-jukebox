import http.server
import socketserver

PORT = 4040
SUBSONIC_TARGET = 'proton:4040'
HARD_REDIRECT = False


class SubsonicRelay (http.server.BaseHTTPRequestHandler):
		
	def do_GET(self):
		if self.path.startswith('/rest/'):
			print(self.path)
			self.send_response(301 if HARD_REDIRECT else 307)
			self.send_header('Location','http://%s%s' % (SUBSONIC_TARGET, self.path))
			self.end_headers()
		else:
			print('else: %s' % self.path)
			pass

def main():
	with socketserver.TCPServer(("localhost", PORT), SubsonicRelay) as httpd:
		print("serving at port", PORT)
		httpd.serve_forever()

if __name__ == '__main__':
	main()

