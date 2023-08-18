from django.urls import path

from cowork import consumers

websocket_urlpatterns = [
    path('chat/<str:room_slug>/', consumers.ChatConsumer.as_asgi()),
]
