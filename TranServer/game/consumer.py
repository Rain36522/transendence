import json
from channels.generic.websocket import AsyncWebsocketConsumer
from tournament.consumer import getUpdate
from .models import Game, GameUser
from tournament.consumer import TournamentConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from django.middleware.csrf import get_token
from sys import stderr


"""Game ws manager
Manage the connection between game server and django.
Send tournament update in case of tournament game end.
Also set the winer as next game player
"""

class GameServerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.path = self.scope['path']
        self.group_name = "gameServer"
        self.channel_layer = get_channel_layer()

        # Ajoute le consommateur WebSocket au groupe
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Implement any necessary cleanup logic here
        await self.channel_layer.group_discard("gameServer", self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # Here you should handle incoming messages, but for now, let's just send a response back
        print("TEXT DATA : ", text_data, file=stderr)
        data = json.loads(text_data)
        game_id = data["gameid"]
        game = await sync_to_async(Game.objects.get)(pk=game_id)
        winner = await self.putGameResultDb(game, data)
        await self.tournamentEndGame(game, winner)
    
    async def game_msg(self, event):
        message = event['message']  # Accéder au message dans l'événement
        await self.send(text_data=json.dumps({"message": message}))

    @sync_to_async    
    def tournamentEndGame(self, game, winner):
        if game.tournament and winner:
            tournamentId = game.tournament.id
            if game.nextGame:
                nextGame = game.nextGame
                GameUser.objects.create(user=winner.user, game=nextGame)
                if nextGame.gameuser_set.count() == nextGame.gamemode * 2:
                    launchGame(nextGame)
            if tournamentId:
                async_to_sync(self.sendUpdateTournamentview)(tournamentId)
                
    @sync_to_async
    def putGameResultDb(self, game, data): #return winner
        if game.gamemode > 0:
            maxPoint = 0
            winner = None
            game.gameRunning = False
            gameusers = game.gameuser_set.all()
            for cle, value in data.items():
                if cle.startswith("user") and value[1] > maxPoint:
                    maxPoint = value[1]
            for gameuser in gameusers:
                for cle, value in data.items():
                    if cle.startswith("user") and value[0] == gameuser.user.username:
                        if game.tournament and game.levelPos == 0 and maxPoint > 1:
                            gameuser.user.total_tournaments += 1
                        gameuser.points = value[1]
                        if maxPoint > 1:
                            gameuser.user.total_games += 1
                        if maxPoint == value[1]:
                            winner = gameuser
                        break
            if winner and winner.points > 1:
                winner.user.wins += 1
                if game.tournament and not game.nextGame:
                    winner.user.tournaments_wins += 1
            for gameuser in gameusers:
                gameuser.user.save()
                gameuser.save()

            game.save()
            return winner
        return None

    async def sendUpdateTournamentview(self, tournamentId):
        data = await getUpdate(tournamentId)
        await self.channel_layer.group_send(
            'tournament_' + str(tournamentId),
            {
                'type': 'send_update',
                'data': data,
            }
            )
        
    async def send_data(self, event):
        data = event["data"]
        await self.send(text_data=json.dumps(data))


"""Launch game instance
This class take the information and send for launching a game instance.
"""
class launchGame:
    def __init__(self, game):
        self.chanelLayer = get_channel_layer()
        data = self.generateGame(game, self.generateDico(game))
        self.sendData(data)
        game.gameRunning = True
        game.save()

    def generateDico(self, game):
        dico = {}
        dico["gameid"] = game.id
        dico["ballwidth"] = game.ballwidth
        dico["planksize"] = game.planksize
        dico["Speed"] = game.Speed
        dico["winpoint"] = game.winpoint
        dico["gamemode"] = game.gamemode
        if game.tournament:
            dico["tournamentid"] = game.tournament.id
        else:
            dico["tournamentid"] = 0
        return dico
    
    def generateGame(self, game, dico):
        if game.gamemode == 1: #2p offline, 2p online
            dico["playeramount"] = 2
        elif game.gamemode == 2: # 4p
            dico["playeramount"] = 4
        else: #game.gamemode = 3 = IA
            dico["playeramount"] = 1
        users = game.gameuser_set.all().values_list('user__username', flat=True)
        i = 0
        for user in users:
            dico["user{}".format(i)] = user
            i += 1
        return dico
    
    def sendData(self, data):
        async_to_sync(self.chanelLayer.group_send)(
            'gameServer',
            {
                'type': 'game_msg',
                'message': data,
            }
        )
