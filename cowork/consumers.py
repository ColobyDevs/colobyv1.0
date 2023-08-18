import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.shortcuts import get_object_or_404
from asgiref.sync import sync_to_async
from cowork.models import Room, Message

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room = None
        self.user = None

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_slug"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]
        self.room = await self.get_or_create_room(self.room_name)
        
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        
        await self.add_user_to_room(self.room, self.user)
        await self.accept()

    async def disconnect(self, close_code):
        await self.remove_user_from_room(self.room, self.user)
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        username = self.user.username

        await self.save_message(self.room, self.user, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "username": username,
            }
        )

    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]
        message_html = f"{message}"
        await self.send(
            text_data=json.dumps(
                {
                    "message": message_html,
                    "username": username
                }
            )
        )

    @sync_to_async
    def save_message(self, room, user, message):
        Message.objects.create(room=room, user=user, message=message)

    @sync_to_async
    def get_or_create_room(self, slug):
        return get_object_or_404(Room, slug=slug)

    @sync_to_async
    def add_user_to_room(self, room, user):
        if user not in room.users.all():
            room.users.add(user)
            room.save()

    @sync_to_async
    def remove_user_from_room(self, room, user):
        if user in room.users.all():
            room.users.remove(user)
            room.save()
