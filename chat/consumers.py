import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from .models import ChatMessage
from channels.db import database_sync_to_async
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "group_chat_gfg"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send message history to new connection
        if not isinstance(self.scope['user'], AnonymousUser):
            await self.send_existing_messages()

    @database_sync_to_async
    def get_latest_messages(self):
        """Retrieve the 50 most recent messages from database"""
        # First get the count to determine offset
        total_messages = ChatMessage.objects.filter(
            room_name=self.room_group_name
        ).count()
        
        # Calculate offset (we want last 50 messages)
        offset = max(0, total_messages - 50)
        
        # Get the last 50 messages ordered chronologically
        return list(ChatMessage.objects.filter(
            room_name=self.room_group_name
        ).select_related('user').order_by('timestamp')[offset:])

    async def send_existing_messages(self):
        """Send the 50 most recent messages to the newly connected client"""
        messages = await self.get_latest_messages()
        for message in messages:
            await self.send(text_data=json.dumps({
                'type': 'message',
                'message': message.message,
                'username': message.user.username,
                'timestamp': message.timestamp.isoformat()
            }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'message':
                await self.handle_message(text_data_json)
            elif message_type == 'typing':
                await self.handle_typing(text_data_json)
            elif message_type == 'stop_typing':
                await self.handle_stop_typing(text_data_json)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "Invalid JSON format"
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                "error": f"An error occurred: {str(e)}"
            }))

    @database_sync_to_async
    def save_message(self, message, user):
        """Save message to database"""
        return ChatMessage.objects.create(
            room_name=self.room_group_name,
            user=user,
            message=message
        )

    async def handle_message(self, data):
        """Handle incoming chat messages"""
        message = data["message"]
        username = data["username"]
        
        # Save message to database if user is authenticated
        if not isinstance(self.scope['user'], AnonymousUser):
            chat_message = await self.save_message(message, self.scope['user'])
            timestamp = chat_message.timestamp.isoformat()
        else:
            timestamp = timezone.now().isoformat()
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "username": username,
                "timestamp": timestamp
            }
        )

    async def handle_typing(self, data):
        """Handle typing notification"""
        username = data["username"]
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_indicator",
                "username": username,
                "is_typing": True
            }
        )

    async def handle_stop_typing(self, data):
        """Handle stop typing notification"""
        username = data["username"]
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_indicator",
                "username": username,
                "is_typing": False
            }
        )

    async def chat_message(self, event):
        """Receive message from room group and send to WebSocket"""
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": event["message"],
            "username": event["username"],
            "timestamp": event["timestamp"]
        }))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        await self.send(text_data=json.dumps({
            "type": "typing",
            "username": event["username"],
            "is_typing": event["is_typing"]
        }))