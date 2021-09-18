import asyncio
import websockets
import json

async def hello():
  async with websockets.connect('ws://localhost:9001') as websocket:
    while True:
      try:
        msg = await websocket.recv()
        print("> {}".format(msg))

        return_msg = json.loads(msg)
        # TODO Encode body as base64 string
        return_msg["body"] = "This is the response!"

        await websocket.send(json.dumps(return_msg))
        print("< {}".format(json.dumps(return_msg)))
      except websockets.ConnectionClosed:
        print(f"Terminated")
        break

asyncio.get_event_loop().run_until_complete(hello())