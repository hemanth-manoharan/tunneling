import asyncio
import aiohttp
import websockets
import json
import base64

local_svc = "http://localhost:9002"

bin_types = ["image/jpeg"]
def is_text(headers):
  if headers.get("content-type") in bin_types:
    return False
  else:
    return True

def get_headers_json(headers):
  # TODO Implement function correctly
  return {
    "content-type": headers["content-type"],
    "content-length": headers["content-length"]
  }

async def hello():
  async with websockets.connect("ws://localhost:9001") as websocket:
    while True:
      try:
        req_msg = await websocket.recv()
        print("> {}".format(req_msg))

        # Make the call using aiohttp
        # https://docs.aiohttp.org/en/stable/client_quickstart.html
        req_msg_json = json.loads(req_msg)
        if req_msg_json["method"] == "GET":
          async with aiohttp.ClientSession() as session:
            async with session.get(local_svc + req_msg_json["uri"]) as resp:
              print("Response status from svc: " + str(resp.status))
              print("Response headers: " + str(resp.headers))
              is_text_resp = is_text(resp.headers)
              if is_text_resp:
                resp_body = await resp.text()
              else:
                resp_body_bytes = await resp.read()
                resp_body = base64.b64encode(resp_body_bytes).decode('utf-8')

        # TODO Construct new resp object here
        return_msg = req_msg_json

        return_msg["headers"] = get_headers_json(resp.headers)
        return_msg["body"] = resp_body
        await websocket.send(json.dumps(return_msg))
        
      except websockets.ConnectionClosed:
        print(f"Terminated")
        break

asyncio.get_event_loop().run_until_complete(hello())