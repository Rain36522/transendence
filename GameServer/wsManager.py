from wsServer import WebSocketServer
from wsDjangoCli import DjangoCli
import wsServer
import asyncio


if __name__ == "__main":
    django = "ws://127.0.0.1:8000"
    Serveur = WebSocketServer("0.0.0.0", 8001)
    djangoCli = DjangoCli(Serveur)

    asyncio.get_event_loop().run_until_complete(djangoCli.connectDjango())

    asyncio.get_event_loop().create_task(Serveur.start_server())
    asyncio.get_event_loop().create_task(djangoCli.receive_messages())
    asyncio.get_event_loop().create_task(djangoCli.sendDjangoMsg())




# if __name__ == "__main__":
#     #waiting wsServeur start for auto start test
#     sleep(3)
#     wsServ = "ws://localhost:8001/game/1"
#     # Création d'un client WebSocket
#     #client = WebSocketClient("ws://localhost:8001/game/" + gameSettings["gameid"])
#     client = WebSocketClient(wsServ)

#     # Lancement du client WebSocket en parallèle
#     asyncio.get_event_loop().run_until_complete(client.connect())
#     asyncio.get_event_loop().create_task(client.receive_messages())

    # Lancement de la boucle d'événements asyncio pour attendre la connexion
    # Création d'une tâche pour exécuter une autre fonction en parallèle
    gameLogicInstance = gameLogic(client, gameSettings, game)
    asyncio.get_event_loop().create_task(gameLogicInstance.gameInput())

    # Lancement de la boucle d'événements asyncio
    asyncio.get_event_loop().run_forever()