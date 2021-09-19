from http.server import SimpleHTTPRequestHandler, HTTPServer

http_server_port = 9002
httpd = HTTPServer(('', http_server_port), SimpleHTTPRequestHandler)
httpd.serve_forever()
