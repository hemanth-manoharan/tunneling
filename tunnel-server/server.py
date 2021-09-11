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

httpServerPort = 9000
httpd = HTTPServer(('', httpServerPort), HttpReqHandler)

def http_serve_forever(httpd):
  with httpd:  # to make sure httpd.server_close is called
    logging.info('Starting http server...\n')
    httpd.serve_forever()

thread = Thread(target=http_serve_forever, args=(httpd, ))
thread.start()

# Start the WebSocket server thread
# Reference: https://websockets.readthedocs.io/en/3.0/intro.html

connectedWS = None

async def client_regn_handler(websocket, path):
  global connectedWS

  connectedWS = websocket

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


wssPort = 9001
wssd = websockets.serve(client_regn_handler, 'localhost', wssPort)

logging.info('Starting wss server...\n')
asyncio.get_event_loop().run_until_complete(wssd)
asyncio.get_event_loop().run_forever()
