import asyncio
import aiohttp
import websockets
import json

local_svc = "http://localhost:9002"

async def hello():
  async with websockets.connect('ws://localhost:9001') as websocket:
    while True:
      try:
        req_msg = await websocket.recv()
        print("> {}".format(req_msg))

        # Make the call using aiohttp
        # https://docs.aiohttp.org/en/stable/client_quickstart.html
        # TODO Send headers
        req_msg_json = json.loads(req_msg)
        if req_msg_json["method"] == "GET":
          async with aiohttp.ClientSession() as session:
            async with session.get(local_svc + req_msg_json["uri"]) as resp:
              print("Response status from svc: " + str(resp.status))
              resp_body = await resp.text()

        return_msg = req_msg_json
        # TODO Encode body as base64 string
        # TODO Support for binary payloads
        return_msg["body"] = resp_body

        await websocket.send(json.dumps(return_msg))
        print("< {}".format(json.dumps(return_msg)))
      except websockets.ConnectionClosed:
        print(f"Terminated")
        break

asyncio.get_event_loop().run_until_complete(hello())