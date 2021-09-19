# Thanks to
# https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7
# https://gist.github.com/kwk/5387c0e8d629d09f93665169879ccb86
# for the core concepts!

from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

import asyncio
import websockets
import time
import json
import base64

from threading import Thread

logging.basicConfig(level=logging.INFO)

bin_types = ["image/jpeg"]
def is_text(headers):
  if headers.get("content-type") in bin_types:
    return False
  else:
    return True

event_dict = {}
resp_dict = {}

# Thread-safe version of asyncio.Event
# Ref: https://stackoverflow.com/questions/33000200/asyncio-wait-for-event-from-other-thread
class Event_ts(asyncio.Event):
  #TODO: clear() method
  def set(self):
    #FIXME: The _loop attribute is not documented as public api!
    self._loop.call_soon_threadsafe(super().set)

# JSON payload structure over the WebSocket
# Request/Response message format
# {
#   "id": "<unique request id>",
#   "uri": "<uri of request>",
#   "method": "<HTTP METHOD>",
#   "headers": {
#   },
#   "body": "<body encoded as base64 string>"
# }
class HttpReqHandler(BaseHTTPRequestHandler):
  def _set_text_response(self):
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()

  def _set_bin_response(self, headers):
    self.send_response(200)
    self.send_header('content-type', headers["content-type"])
    self.send_header('content-length', headers["content-length"])
    self.end_headers()

  def gen_unique_id(self):
    return time.time()

  async def handle_get(self, path, headers):
    global event_dict
    global resp_dict

    if connected_ws != None:
      event = Event_ts()
       
      msg_id = self.gen_unique_id()
      # TODO send headers as well
      msg = {
        "id": msg_id,
        "uri": path,
        "method": "GET"
      }
      event_dict[msg_id] = event
 
      await connected_ws.send(json.dumps(msg))
      logging.debug("> {}".format(json.dumps(msg)))

      # Wait on this event to be triggered
      # TODO Put in timeouts for resilience
      logging.info("Starting to wait on event with id: {}".format(msg_id))
      await event.wait()
      logging.info("Finished waiting on event with id: {}".format(msg_id))

      # Retrieve response and return
      response = resp_dict[msg_id]
      del resp_dict[msg_id]
      return response

    return None

  def do_GET(self):
    logging.debug("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))

    # Wait for the response
    # Ref: https://geekyhumans.com/create-asynchronous-api-in-python-and-flask/

    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(self.handle_get(str(self.path), self.headers))

    logging.debug("Resp Headers from client:" + str(result["headers"]))

    is_text_resp = is_text(result["headers"])
    if is_text_resp:
      self._set_text_response()
      self.wfile.write(result["body"].encode('utf-8'))
    else:
      self._set_bin_response(result["headers"])
      self.wfile.write(base64.b64decode(result["body"]))

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

      msg_json = json.loads(msg)
      msg_id = msg_json["id"]

      # Fetch by unique request id
      # Put response in dict and raise event
      if msg_id in event_dict:
        logging.info("Found event dict entry with id: {}".format(msg_id))
        resp_dict[msg_id] = msg_json
        event_dict[msg_id].set()
        logging.info("Deleting event entry from dict with id: {}".format(msg_id))
        del event_dict[msg_id]

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
