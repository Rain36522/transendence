from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer  # Import JSONRenderer
from rest_framework import status
from django.http import JsonResponse, HttpResponse
from .models import Game, GameUser
from rest_framework.views import APIView
from .serializers import GameSettingsSerializer
from asgiref.sync import async_to_sync
import sys
from time import time
import asyncio
from channels.layers import get_channel_layer
import json
from .consumer import launchGame


# @login_required
class newGame(APIView):
    def get(self, request):
        print("GET", file=sys.stderr)
        return render(request, 'gamesettinspage.html')
    
    def post(self, request):
        print("POST", file=sys.stderr)
        data = self.changeData(request.data.copy())
        if data:
            serializer = GameSettingsSerializer(data=data)
            if serializer.is_valid():
                instance = serializer.save()  # Enregistre les données et récupère l'objet sauvegardé
                self.addPlayer(instance)
                launchGame(instance)
                return redirect(f'/game' + str(instance.id))
        return HttpResponse("Error 400", status=400)
    
    def changeData(self, data):
        if data.get("ballwidth") and data.get("planksize") and data.get("Speed") and data.get("acceleration"):
            data["ballwidth"] = int(data["ballwidth"]) / 100
            data["planksize"] = int(data["planksize"]) / 100
            if int(data["acceleration"]):
                data["acceleration"] = int(data["acceleration"]) / 100
            return data
        return None

    def sendNewGame(self, data):
        print("sending new msg")
        data = json.dumps(data)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
        "",
        {
            "type": "send_data",
            "data": data,
        }
        )
        print("message send")

    def addPlayer(self, game):
        user = GameUser.objects.create(user=user, game=game)
        game.gameuser_set.add(user)

def gamePage(request, id):
    return HttpResponse("Success")

def home_page(request):
    return render(request, 'html/home.html')

def online_game(request):
    return render(request, 'html/onlineGame.html')

