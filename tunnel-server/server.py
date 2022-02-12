"""
Tunneling Server

This script proxies http requests from the upstream
Caddy reverse proxy down as messages via a Web Socket
to the tunneling client. It also proxies the response
messages from the Web Socket (from the tunneling client)
back to the Caddy reverse proxy.
"""

import logging
import asyncio
import configparser
import time
import json
import base64
from threading import Thread
import aiohttp
from multidict import CIMultiDictProxy

import websockets
from aiohttp import web

# Global initialization
config = configparser.ConfigParser()
config.read('config.ini')
logging.basicConfig(level=config["general"]["LoggingLevel"])

event_dict = {}
resp_dict = {}
connected_ws = None


class EventTs(asyncio.Event):
    """
    Thread-safe version of asyncio.Event

    Ref: https://stackoverflow.com/questions/33000200/asyncio-wait-for-event-from-other-thread
    """

    #TODO: clear() method
    def set(self):
        #FIXME: The _loop attribute is not documented as public api!
        self._loop.call_soon_threadsafe(super().set)


def get_headers_dict(headers: CIMultiDictProxy) -> dict:
    """
    Converts the headers dictionary to a normal serializable dictionary
    """

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


async def handle_request(request: aiohttp.web.Request):
    """
    Proxies the incoming http request via the web socket

    Extracts the incoming http request and then proxies it
    via the web socket. It then awaits the response from the
    web socket in a async fashion and then finally returns the 
    response.
    """

    global event_dict
    global resp_dict
    global connected_ws

    if connected_ws is not None:
        msg = await _get_req_msg(request)
        event = EventTs()
        event_dict[msg["id"]] = event

        await connected_ws.send(json.dumps(msg))
        logging.debug('> %s', json.dumps(msg))

        # Wait on this event to be triggered
        # TODO Put in timeouts for resilience
        logging.info('Waiting on event for req id: %f', msg["id"])
        await event.wait()
        logging.info('Event received for req id: %f', msg["id"])

        # Retrieve response and return
        ws_response = resp_dict[msg["id"]]
        del resp_dict[msg["id"]]
        return ws_response

    return None


async def all_handler(
        request: aiohttp.web.Request) -> aiohttp.web.StreamResponse:
    """
    asyncio handler for all the http requests received from the reverse proxy
    """

    ws_response = await handle_request(request)
    return web.Response(body=base64.b64decode(ws_response["body"]),
                        headers=ws_response["headers"],
                        status=int(ws_response["status"]))


app = web.Application()
app.add_routes([
    web.route('*', '/{uri:.*}', all_handler),
])


async def socket_server_handler(websocket, path):
    """
    Handler for the server-side web-socket connection

    Reference: https://websockets.readthedocs.io/en/stable/intro/index.html
    """

    global connected_ws
    global event_dict
    global resp_dict

    connected_ws = websocket

    while True:
        try:
            msg = await websocket.recv()
            logging.debug("< %s", msg)

            msg_json = json.loads(msg)
            msg_id = msg_json["id"]

            # Fetch by unique request id
            # Put response in dict and raise event
            if msg_id in event_dict:
                logging.info("Found event dict entry with id: %f", msg_id)
                resp_dict[msg_id] = msg_json
                event_dict[msg_id].set()
                logging.info("Deleting event entry from dict with id: %f",
                             msg_id)
                del event_dict[msg_id]

        except websockets.ConnectionClosed:
            logging.info("WebSocket connection terminated")
            connected_ws = None
            break


# Start the external WebSocket server
wss_port = config["general"]["WebSocketServerPort"]


async def wss_main():
    """
    Main logic / indefinite loop for the Web Socket Server
    """

    # TODO Allow localhost to be configured. For DigitalOcean, replace with Droplet public IP
    async with websockets.serve(socket_server_handler, "localhost", wss_port):
        await asyncio.Future()  # run forever


def serve_forever():
    """
    Indefinite event loop for the Web Socket Server
    """

    logging.info('Starting wss server...\n')
    asyncio.run(wss_main())


# Spawn a separate thread for the Web Socker Server
# Primary thread is reserved for the Http Server
thread = Thread(target=serve_forever)
thread.start()

logging.info('Starting http server...\n')
http_server_port = int(config["general"]["HttpServerPort"])
web.run_app(app, port=http_server_port)
