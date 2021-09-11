import asyncio
import websockets

async def hello():
  async with websockets.connect('ws://localhost:9001') as websocket:
    while True:
      try:
        name = input("What's your name? ")
        await websocket.send(name)
        print("> {}".format(name))

        greeting = await websocket.recv()
        print("< {}".format(greeting))
      except websockets.ConnectionClosed:
        print(f"Terminated")
        break

asyncio.get_event_loop().run_until_complete(hello())