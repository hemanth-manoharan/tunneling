import logging

import asyncio
import configparser
import websockets
import time
import json
import base64

from threading import Thread

from aiohttp import web

# Global initialization
config = configparser.ConfigParser()
config.read('config.ini')
logging.basicConfig(level=config["general"]["LoggingLevel"])

event_dict = {}
resp_dict = {}
connected_ws = None

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

def _gen_unique_id():
  return time.time()

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
async def _get_req_msg(request):
  msg_id = _gen_unique_id()
  msg = {
    "id": msg_id,
    "uri": request.path,
    "method": request.method,
    "headers": get_headers_dict(request.headers)
  }

  if request.can_read_body:
    body = await request.read()
    body_encoded = base64.b64encode(body).decode('utf-8')
    msg["body"] = body_encoded

  return msg

async def handle_request(request):
  global event_dict
  global resp_dict
  global connected_ws

  if connected_ws != None:
    msg = await _get_req_msg(request)
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
    ws_response = resp_dict[msg["id"]]
    del resp_dict[msg["id"]]
    return ws_response

  return None

def get_http_response(ws_response):
  if ws_response["is_text"]:
    return web.Response(
      text=ws_response["body"],
      headers=ws_response["headers"],
      status=int(ws_response["status"])
    )
  else:
    return web.Response(
      body=base64.b64decode(ws_response["body"]),
      headers=ws_response["headers"],
      status=int(ws_response["status"])
    )  

# asyncio http server handler
async def all_handler(request):
  ws_response = await handle_request(request)
  return get_http_response(ws_response)

app = web.Application()
app.add_routes([
  web.route('*', '/{uri:.*}', all_handler),
  ])

# Reference: https://websockets.readthedocs.io/en/stable/intro/index.html

async def socket_server_handler(websocket, path):
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
  async with websockets.serve(socket_server_handler, "localhost", wss_port):
    await asyncio.Future()  # run forever

def serve_forever():
  logging.info('Starting wss server...\n')
  asyncio.run(wss_main())

thread = Thread(target=serve_forever)
thread.start()

logging.info('Starting http server...\n')
http_server_port = int(config["general"]["HttpServerPort"])
web.run_app(app, port = http_server_port)
