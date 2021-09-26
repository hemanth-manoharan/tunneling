import asyncio
import aiohttp
import websockets
import json
import logging
from httputil import *

# TODO Read from env variable
local_svc = "http://localhost:9002"

logging.basicConfig(level=logging.INFO)

async def tunnelling_client_loop():
  async with websockets.connect("ws://localhost:9001") as websocket:

    session = aiohttp.ClientSession()

    while True:
      try:
        req_msg = await websocket.recv()
        logging.debug("> {}".format(req_msg))

        # Make the call using aiohttp
        # https://docs.aiohttp.org/en/stable/client_quickstart.html
        req_msg_json = json.loads(req_msg)
        if req_msg_json["method"] == "GET":
          async with session.get(local_svc + req_msg_json["uri"]) as resp:
            resp_status, resp_headers, resp_body = await extract_response_details(resp, logging)
        elif req_msg_json["method"] == "POST":
          # TODO Convert message body to right format before making the call
          async with session.post(local_svc + req_msg_json["uri"], data = req_msg["body"]) as resp:
            resp_status, resp_headers, resp_body = await extract_response_details(resp, logging)
        is_text_resp = is_text(resp.headers)

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
        print(f"Terminated")
        break

    await session.close()

asyncio.get_event_loop().run_until_complete(tunnelling_client_loop())