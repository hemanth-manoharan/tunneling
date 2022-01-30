import asyncio
import aiohttp
import configparser
import websockets
import json
import logging
import base64
from httputil import *

config = configparser.ConfigParser()
config.read('config.ini')
logging.basicConfig(level=config["general"]["LoggingLevel"])
local_svc = config["local-service"]["ServiceURL"]

async def tunnelling_client_loop():
  async with websockets.connect(config["tunnelling-server"]["WebSocketURL"]) as websocket:

    session = aiohttp.ClientSession()

    while True:
      try:
        logging.debug("Waiting for next message ...")
        req_msg = await websocket.recv()
        logging.debug("> {}".format(req_msg))

        # Make the call using aiohttp
        # https://docs.aiohttp.org/en/stable/client_quickstart.html
        req_msg_json = json.loads(req_msg)
        if req_msg_json["method"] == "GET":
          async with session.get(local_svc + req_msg_json["uri"], headers=req_msg_json["headers"]) as resp:
            resp_status, resp_headers, resp_body = await extract_response_details(resp, logging)
        elif req_msg_json["method"] == "POST":
          # TODO Convert message body to right format before making the call
          # TODO call base64.b64decode(req_msg_json["body"]) if request body is b64 encoded
          async with session.post(local_svc + req_msg_json["uri"],
            data = base64.b64decode(req_msg_json["body"]), headers = req_msg_json["headers"]) as resp:
            resp_status, resp_headers, resp_body = await extract_response_details(resp, logging)

        is_text_resp = is_text(resp.headers)
        if is_text_resp:
          logging.debug("Sending text response...")
        else:
          logging.debug("Sending binary response...")

        # Construct new resp object here
        return_msg = {
          "id": req_msg_json["id"],
          "status": resp_status,
          "is_text": is_text_resp,
          "headers": resp_headers,
          "body": resp_body
        }

        await websocket.send(json.dumps(return_msg))

      except websockets.ConnectionClosed:
        logging.info(f"Exception: WebSocket connection closed...")
        break

    await session.close()

asyncio.get_event_loop().run_until_complete(tunnelling_client_loop())