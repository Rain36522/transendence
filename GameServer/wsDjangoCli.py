import asyncio
import websockets
import os
import sys
from wsServer import WebSocketServer
from time import sleep

class DjangoCli:
    def __init__(self, wsServer):
        self.websocket = None
        self.wsServer = wsServer


    async def connectDjango(self, url):
        i = 0
        while i <= 10: 
            try:
                self.websocket = await websockets.connect(url)
                print("GameServ, connected to Daphne.", file=sys.stderr)
                break
            except:
                print("Server daphne not available.", file=sys.stderr)
                sleep(1)
                i += 1
        if i > 10:
            print("Client fail 10x the connection with daphne ws.", url , file=sys.stderr)

        # Coroutine asynchrone pour lire les messages de manière non bloquante
    async def receive_messages(self):
        i = 0
        while True:
            try:
                message = await self.websocket.recv()
                os.environ['newGame'] = message
                os.system("python3 game/game.py &")
            except websockets.exceptions.ConnectionClosed:
                i += 1
                print("Connection to server django closed")
                if i == 5:
                    break
                else:
                    self.connectDjango()

    async def sendDjangoMsg(self):
        while True:
            messages = self.wsServer.getDjangoMsg()
            if messages:
                for msg in messages:
                    await self.websocket.send(msg)
            asyncio.sleep(0.1)


    async def close_connection(self):
        if self.websocket and self.websocket.open:
            await self.websocket.close()
