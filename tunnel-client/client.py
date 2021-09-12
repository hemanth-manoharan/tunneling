import asyncio
import websockets

async def hello():
  async with websockets.connect('ws://localhost:9001') as websocket:
    while True:
      try:
        msg = await websocket.recv()
        print("> {}".format(msg))

        return_msg = msg + " Response"

        await websocket.send(return_msg)
        print("< {}".format(return_msg))
      except websockets.ConnectionClosed:
        print(f"Terminated")
        break

asyncio.get_event_loop().run_until_complete(hello())