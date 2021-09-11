# Thanks to
# https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7
# https://gist.github.com/kwk/5387c0e8d629d09f93665169879ccb86
# for the core concepts!

from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

import asyncio
import websockets

from threading import Thread

class HttpReqHandler(BaseHTTPRequestHandler):
  def _set_response(self):
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()

  def do_GET(self):
    logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))

    # TODO Send the message over the listening websocket here
    # Synchronously wait for the response (simple design) and
    # return the response back.

    self._set_response()
    self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

  def do_POST(self):
    content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
    post_data = self.rfile.read(content_length) # <--- Gets the data itself
    logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
            str(self.path), str(self.headers), post_data.decode('utf-8'))

    # TODO Send the message over the listening websocket here
    # Synchronously wait for the response (simple design) and
    # return the response back.

    self._set_response()
    self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

logging.basicConfig(level=logging.INFO)

# Start the http server thread

http_server_port = 9000
httpd = HTTPServer(('', http_server_port), HttpReqHandler)

def http_serve_forever(httpd):
  with httpd:  # to make sure httpd.server_close is called
    logging.info('Starting http server...\n')
    httpd.serve_forever()

thread = Thread(target=http_serve_forever, args=(httpd, ))
thread.start()

# Start the WebSocket server
# Reference: https://websockets.readthedocs.io/en/stable/intro/index.html
connected_ws = None

async def client_regn_handler(websocket, path):
  global connected_ws

  connected_ws = websocket

  while True:
    try:
      name = await websocket.recv()
      print("< {}".format(name))

      greeting = "Hello {}!".format(name)
      await websocket.send(greeting)
      print("> {}".format(greeting))
    except websockets.ConnectionClosed:
      print(f"Terminated")
      break

wss_port = 9001

async def wss_main():
    async with websockets.serve(client_regn_handler, "localhost", wss_port):
        await asyncio.Future()  # run forever

logging.info('Starting wss server...\n')
asyncio.run(wss_main())
