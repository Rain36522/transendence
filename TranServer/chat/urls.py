from django.urls import path
from .views import ChatListView, chat_view, MessageListView

urlpatterns = [
     path('chats/', chat_view, name='chats'),
     path('api/chat/', ChatListView.as_view(), name='chat_api'),
     path('api/chat/<str:chat_id>/', ChatListView.as_view(), name='chat_api'),
     path('api/messages/<str:chat_id>/', MessageListView.as_view(), name='chat_message_view')
]