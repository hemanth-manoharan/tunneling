# Thanks to
# https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7
# https://gist.github.com/kwk/5387c0e8d629d09f93665169879ccb86
# for the core concepts!

from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

import asyncio
import websockets

from threading import Thread

logging.basicConfig(level=logging.DEBUG)

event_dict = {}
resp_dict = {}

# Thread-safe version of asyncio.Event
# Ref: https://stackoverflow.com/questions/33000200/asyncio-wait-for-event-from-other-thread
class Event_ts(asyncio.Event):
  #TODO: clear() method
  def set(self):
    #FIXME: The _loop attribute is not documented as public api!
    self._loop.call_soon_threadsafe(super().set)

class HttpReqHandler(BaseHTTPRequestHandler):
  def _set_response(self):
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()

  async def handle_get(self, path):
    global event_dict
    global resp_dict

    if connected_ws != None:
      event = Event_ts()
      
      # Put this event in the in-memory hashmap
      # TODO Just using payload as unique request id
      msg = "GET {}".format(path)
      event_dict[msg + " Response"] = event
 
      await connected_ws.send(msg)
      logging.debug("> {}".format(msg))

      # Wait on this event to be triggered
      # TODO Put in timeouts for resilience
      logging.debug("Starting to wait on event")
      await event.wait()
      logging.debug("Finished waiting on event")

      # Retrieve response and return
      # TODO Change to proper unique request id
      return resp_dict[msg + " Response"]
      del resp_dict[msg + " Response"]

    return None

  def do_GET(self):
    logging.debug("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))

    # Wait for the response
    # Ref: https://geekyhumans.com/create-asynchronous-api-in-python-and-flask/

    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(self.handle_get(str(self.path)))

    self._set_response()
    self.wfile.write("Response: {}".format(result).encode('utf-8'))

  def do_POST(self):
    content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
    post_data = self.rfile.read(content_length) # <--- Gets the data itself
    logging.debug("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
            str(self.path), str(self.headers), post_data.decode('utf-8'))

    # TODO Send the message over the listening websocket here
    # Synchronously wait for the response (simple design) and
    # return the response back.

    self._set_response()
    self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

# Start the http server thread

http_server_port = 9000
httpd = HTTPServer(('', http_server_port), HttpReqHandler)

def http_serve_forever(httpd):
  with httpd:  # to make sure httpd.server_close is called
    logging.info('Starting http server...\n')
    httpd.serve_forever()

thread = Thread(target=http_serve_forever, args=(httpd, ))
thread.start()

# Reference: https://websockets.readthedocs.io/en/stable/intro/index.html
connected_ws = None

async def client_regn_handler(websocket, path):
  global connected_ws
  global event_dict
  global resp_dict

  connected_ws = websocket

  while True:
    try:
      msg = await websocket.recv()
      logging.debug("< {}".format(msg))

      # TODO Fetch by unique request id
      # Put response in dict and raise event
      if msg in event_dict:
        logging.debug("Found event dict entry")
        resp_dict[msg] = msg
        # TODO Not working!!!
        event_dict[msg].set()
        logging.debug("Deleting event entry from dict")
        del event_dict[msg]

    except websockets.ConnectionClosed:
      logging.info(f"WebSocket connection terminated")
      connected_ws = None
      break

# Start the external WebSocket server
wss_port = 9001

async def wss_main():
  async with websockets.serve(client_regn_handler, "localhost", wss_port):
    await asyncio.Future()  # run forever

logging.info('Starting wss server...\n')
asyncio.run(wss_main())
