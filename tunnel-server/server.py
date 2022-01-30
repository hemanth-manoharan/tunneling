# Thanks to
# https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7
# https://gist.github.com/kwk/5387c0e8d629d09f93665169879ccb86
# for the core concepts!

from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

import asyncio
import configparser
import websockets
import time
import json
import base64

from threading import Thread

# Global initialization
config = configparser.ConfigParser()
config.read('config.ini')
logging.basicConfig(level=config["general"]["LoggingLevel"])
event_dict = {}
resp_dict = {}

# Thread-safe version of asyncio.Event
# Ref: https://stackoverflow.com/questions/33000200/asyncio-wait-for-event-from-other-thread
class Event_ts(asyncio.Event):
  #TODO: clear() method
  def set(self):
    #FIXME: The _loop attribute is not documented as public api!
    self._loop.call_soon_threadsafe(super().set)

def get_headers_dict(headers):
  normal_dict = {}

  # TODO Handle for duplicates
  for key in headers.keys():
    # Do not relay transfer-encoding header as it is a per hop header
    if key.lower() == "transfer-encoding":
      continue
    normal_dict[key] = headers[key]
  return normal_dict

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

  def _set_resp_details(self, response):
    self.send_response(int(response["status"]))
    for key in response["headers"].keys():
      self.send_header(key, response["headers"][key])
    self.end_headers()
    if response["is_text"]:
      self.wfile.write(response["body"].encode('utf-8'))
    else:
      self.wfile.write(base64.b64decode(response["body"]))
    self.wfile.flush()
    logging.debug("Finished writing and flushing response...")

  def _get_req_msg(self, body = None):
    msg_id = self._gen_unique_id()
    msg = {
      "id": msg_id,
      "uri": self.path,
      "method": self.command,
      "headers": get_headers_dict(self.headers)
    }
    http_methods_with_body = ["POST", "PUT"]
    if (self.command in http_methods_with_body) and (body != None):
      msg["body"] = body
    return msg

  def _gen_unique_id(self):
    return time.time()

  async def _handle_request(self, body = None):
    global event_dict
    global resp_dict

    if connected_ws != None:
      msg = self._get_req_msg(body)
      event = Event_ts()
      event_dict[msg["id"]] = event
      
      await connected_ws.send(json.dumps(msg))
      logging.debug("> {}".format(json.dumps(msg)))

      # Wait on this event to be triggered
      # TODO Put in timeouts for resilience
      logging.info("Waiting on event for req id: {}".format(msg["id"]))
      await event.wait()
      logging.info("Event received for req id: {}".format(msg["id"]))

      # Retrieve response and return
      response = resp_dict[msg["id"]]
      del resp_dict[msg["id"]]
      return response

    return None
  
  def _do_BASE(self, body = None):
    # Wait for the response
    # Ref: https://geekyhumans.com/create-asynchronous-api-in-python-and-flask/

    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()

    response = loop.run_until_complete(self._handle_request(body))
    logging.debug("Resp Headers from client:" + str(response["headers"]))

    self._set_resp_details(response)

  def do_GET(self):
    logging.debug("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
    self._do_BASE()

  def do_POST(self):
    content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
    req_body = self.rfile.read(content_length) # <--- Gets the data itself
    
    logging.debug("%s request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
            self.command, str(self.path), str(self.headers), req_body.decode('utf-8'))
    self._do_BASE(base64.b64encode(req_body).decode('utf-8'))

  def do_PUT(self):
    self.do_POST()

# Start the http server thread
http_server_port = int(config["general"]["HttpServerPort"])
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
wss_port = config["general"]["WebSocketServerPort"]

async def wss_main():
  # TODO Allow localhost to be configured. For DigitalOcean, replace with Droplet public IP
  async with websockets.serve(client_regn_handler, "localhost", wss_port):
    await asyncio.Future()  # run forever

logging.info('Starting wss server...\n')
asyncio.run(wss_main())
