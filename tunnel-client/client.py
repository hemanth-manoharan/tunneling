import asyncio
import configparser
import json
import logging
import base64
import httputil
import aiohttp
import websockets

config = configparser.ConfigParser()
config.read('config.ini')
logging.basicConfig(level=config["general"]["LoggingLevel"])
local_svc = config["local-service"]["ServiceURL"]


async def tunnelling_client_loop():
    """
    Indefinite loop for Web Socket Client
    """

    async with websockets.connect(
            config["tunnelling-server"]["WebSocketURL"]) as websocket:

        session = aiohttp.ClientSession()

        while True:
            try:
                logging.debug("Waiting for next message ...")
                req_msg = await websocket.recv()
                logging.debug("> %s", req_msg)

                # Make the call using aiohttp
                # https://docs.aiohttp.org/en/stable/client_quickstart.html
                req_msg_json = json.loads(req_msg)
                req_method = req_msg_json["method"]
                if req_method == "GET" or req_method == "DELETE":
                    # TODO DELETE with body scenario not supported yet
                    async with session.request(
                            req_method,
                            local_svc + req_msg_json["uri"],
                            headers=req_msg_json["headers"]) as resp:
                        resp_status, resp_headers, resp_body = await httputil.extract_resp_details(
                            resp, logging)
                elif req_method == "POST" or req_method == "PUT":
                    async with session.request(
                            req_method,
                            local_svc + req_msg_json["uri"],
                            data=base64.b64decode(req_msg_json["body"]),
                            headers=req_msg_json["headers"]) as resp:
                        resp_status, resp_headers, resp_body = await httputil.extract_resp_details(
                            resp, logging)
                else:
                    # TODO Handle this case better
                    logging.error("Unsupported request method. Ignoring ...")
                    continue

                # Construct new resp object here
                return_msg = {
                    "id": req_msg_json["id"],
                    "status": resp_status,
                    "headers": resp_headers,
                    "body": resp_body
                }

                await websocket.send(json.dumps(return_msg))

            except websockets.ConnectionClosed:
                logging.info("Exception: WebSocket connection closed...")
                break

        await session.close()


asyncio.get_event_loop().run_until_complete(tunnelling_client_loop())