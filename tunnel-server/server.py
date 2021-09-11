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

  async def handle_get(self):
    if connected_ws != None:
      await connected_ws.send("GET Request")
      print("> {}".format("GET Request"))
      # TODO Listen for response msg on local MQ
      # # Wait for message to come in
      # msg = await asyncio.wait_for(future, 1)
    return 1

  def do_GET(self):
    logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))

    # TODO Send the message over the listening websocket here
    # Synchronously wait for the response (simple design) and
    # return the response back.
    # Ref: https://geekyhumans.com/create-asynchronous-api-in-python-and-flask/
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(self.handle_get())

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
      msg = await websocket.recv()
      logging.info("< {}".format(msg))
      # TODO Post to local MQ
      # https://docs.nats.io/developing-with-nats/sending
      # await nc.publish("messages", bytes(msg, 'utf-8'))
    except websockets.ConnectionClosed:
      print(f"Terminated")
      connected_ws = None
      break

# TODO
# nc = NATS()
# await nc.connect(servers=["nats://demo.nats.io:4222"])
# https://docs.nats.io/developing-with-nats/receiving/async
# future = asyncio.Future()

# async def cb(msg):
#   nonlocal future
#   future.set_result(msg)

# await nc.subscribe("messages", cb=cb)

wss_port = 9001

async def wss_main():
    async with websockets.serve(client_regn_handler, "localhost", wss_port):
        await asyncio.Future()  # run forever

logging.info('Starting wss server...\n')
asyncio.run(wss_main())
