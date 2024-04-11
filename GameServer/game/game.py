import os
from wsClient import WebSocketClient
from gameLogic import gameLogic
import json
import asyncio
from sys import stderr
from time import sleep
from sys import stderr

# Convertir JSON en dictionnaire
# gameSettings = loads(os.environ.get("newGame"))

#dictionary communication bitween serveur and client.
game = {
	"ballx" : 0, # -0.5 -> 0.5
	"bally" : 0, # -0.5 -> 0.5
	"p1" : 0, # -0.5 -> 0.5
	"p2" : 0, # -0.5 -> 0.5
	"p3" : 0, # -0.5 -> 0.5
	"p4" : 0, # -0.5 -> 0.5
	"state" : "pause",
	"score1" : 0,
	"score2" : 0,
	"score3" : 0,
	"score4" : 0
}

gameSettings = {
    "ballwidth" : 0.03, #max size plank size calculation
    "planksize" : 0.3, #max size 50%
    "Speed" : 0.002,
    "acceleration" : 0.01, #increase speed each bounce
    "playeramount" : 2,
    "winpoint" : 10,
    "user1" : "",
    "user2" : "",
    "user3" : "",
    "user4" : "",
    "gameid" : 0,
}

gameEndDjango = {
    "user1" : ("", 3),
    "user2" : ("", 4),
    "user3" : ("", 5),
    "user4" : ("", 2),
    }


def listUser(data):
    liste = []
    for cle, value in data.items():
        print("data recieve django : ", cle, value, file=stderr)
        if cle.startswith("user"):
            if value:
                print("data accepted as user : ", cle, value, file=stderr)
                liste.append(value)
    return liste

async def WaitUntilPlayers(ws, data):
    userlist = listUser(data)
    liste = []
    while len(liste) < data["playeramount"]:
        msgs = ws.getMsg()
        if msgs:
            for msg in msgs:
                print("New msg", file=stderr)
                if msg.endswith("login"):
                    msg = msg[:-5]
                    print("NewUser : ", msg, file=stderr)
                    if userlist:
                        playerFree = data["playeramount"] - len(userlist)
                    else:
                        playerFree = data["playeramount"]
                    if userlist and msg in userlist:
                        print("add recomanded", file=stderr)
                        liste.append(msg)
                        userlist.remove(msg)
                    elif liste and len(liste) < playerFree and msg not in liste:
                        print("add free", file=stderr)
                        liste.append(msg)
                    elif not liste and playerFree:
                        print("add free", file=stderr)
                        liste.append(msg)

        await asyncio.sleep(0.1)
    print("ALL USER JOIN", file=stderr)
    await asyncio.sleep(1)
    await ws.sendUserJoin(liste)


def putDatagameSettings(data, settings):
    elem = ["ballwidth", "planksize", "Speed", "acceleration", "playeramount", "winpoint", "user1", "user2", "user3", "user4", "gameid"]
    if not data.get("gameid"):
        print("\033[31mGameid not available.\033[0m", file=stderr)
        exit(1)
    for i in elem:
        if data.get(i):
            settings[i] = data[i]
    return settings

# Exemple d'utilisation du client WebSocket avec asyncio
if __name__ == "__main__":
    DjangoData = json.loads(os.environ.get("newGame"))["message"]
    print("Django data : ", DjangoData)
    gameSettings = putDatagameSettings(DjangoData, gameSettings)
    #connection with websocket server
    wsServ = "ws://localhost:8001/game/" + str(gameSettings["gameid"])
    client = WebSocketClient(wsServ)
    # Lancement du client WebSocket en parallèle
    asyncio.get_event_loop().run_until_complete(client.connect())
    asyncio.get_event_loop().create_task(client.receive_messages())
    asyncio.get_event_loop().run_until_complete(WaitUntilPlayers(client, DjangoData))
    # Lancement de la boucle d'événements asyncio pour attendre la connexion
    # Création d'une tâche pour exécuter une autre fonction en parallèle
    gameLogicInstance = gameLogic(client, gameSettings, game)
    asyncio.get_event_loop().create_task(gameLogicInstance.gameInput())

    # Lancement de la boucle d'événements asyncio
    asyncio.get_event_loop().run_forever()