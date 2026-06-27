import json
import asyncio
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from .models import ChatGroup, Message, MessageType
from .serializers import MessageSerializer
from .services import create_message, edit_message, delete_message

# Simple in-memory tracking of online users (for development)
# In production, use Redis
_online_users = {}


def build_absolute_uri(path):
    """Build absolute URI from a relative path using settings."""
    if not path:
        return None
    if path.startswith('http://') or path.startswith('https://'):
        return path
    base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
    return f'{base_url}{path}'


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time chat messaging.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_id = None
        self.group_name = None
        self.user = None
        self.rate_limit_timestamps = []

    async def connect(self):
        """
        Handle WebSocket connection.
        """
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.group_name = f'group_{self.group_id}'
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Verify group exists
        group_exists = await self.check_group_exists()
        if not group_exists:
            await self.close(code=4004)
            return

        # Join channel group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Add user to online users
        user_id = str(self.user.id)
        if self.group_id not in _online_users:
            _online_users[self.group_id] = set()
        _online_users[self.group_id].add(user_id)

        # Broadcast online count
        await self.broadcast_online_count()

        # Send connection success message with current online count
        count = len(_online_users.get(self.group_id, set()))
        await self.send_json({
            'type': 'connection_established',
            'group_id': self.group_id,
            'user_id': user_id,
            'online_count': count
        })

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

            # Remove user from online users
            user_id = str(self.user.id) if self.user else None
            if user_id and self.group_id in _online_users:
                _online_users[self.group_id].discard(user_id)
                # Clean up empty groups
                if not _online_users[self.group_id]:
                    del _online_users[self.group_id]

            # Broadcast updated online count
            await self.broadcast_online_count()

    async def receive_json(self, content):
        """
        Handle incoming JSON messages.
        """
        message_type = content.get('type')

        # Rate limiting
        if not await self.check_rate_limit():
            await self.send_json({
                'type': 'error',
                'message': 'Rate limit exceeded. Please slow down.'
            })
            return

        try:
            if message_type == 'send_message':
                await self.handle_send_message(content)
            elif message_type == 'edit_message':
                await self.handle_edit_message(content)
            elif message_type == 'delete_message':
                await self.handle_delete_message(content)
            else:
                await self.send_json({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                })
        except Exception as e:
            await self.send_json({
                'type': 'error',
                'message': str(e)
            })

    async def handle_send_message(self, content):
        """
        Handle sending a new message.
        """
        group = await self.get_group()
        if not group:
            await self.send_json({
                'type': 'error',
                'message': 'Group not found'
            })
            return

        message_content = content.get('content', '')
        msg_type = content.get('message_type', 'TEXT')

        try:
            message = await database_sync_to_async(create_message)(
                user=self.user,
                group=group,
                content=message_content,
                message_type=msg_type
            )

            message_data = await database_sync_to_async(lambda: MessageSerializer(message).data)()

            # Convert avatar URLs to absolute URIs
            if message_data.get('sender_info', {}).get('avatar'):
                message_data['sender_info']['avatar'] = build_absolute_uri(message_data['sender_info']['avatar'])

            # Broadcast to group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'new_message',
                    'message': message_data
                }
            )
        except Exception as e:
            await self.send_json({
                'type': 'error',
                'message': str(e)
            })

    async def handle_edit_message(self, content):
        """
        Handle editing a message.
        """
        message_id = content.get('message_id')
        new_content = content.get('content', '')

        if not message_id:
            await self.send_json({
                'type': 'error',
                'message': 'message_id is required'
            })
            return

        try:
            message = await database_sync_to_async(edit_message)(
                user=self.user,
                message_id=message_id,
                new_content=new_content
            )

            message_data = await database_sync_to_async(lambda: MessageSerializer(message).data)()

            # Convert avatar URLs to absolute URIs
            if message_data.get('sender_info', {}).get('avatar'):
                message_data['sender_info']['avatar'] = build_absolute_uri(message_data['sender_info']['avatar'])

            # Broadcast to group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'message_updated',
                    'message': message_data
                }
            )
        except Exception as e:
            await self.send_json({
                'type': 'error',
                'message': str(e)
            })

    async def handle_delete_message(self, content):
        """
        Handle deleting a message.
        """
        message_id = content.get('message_id')

        if not message_id:
            await self.send_json({
                'type': 'error',
                'message': 'message_id is required'
            })
            return

        try:
            await database_sync_to_async(delete_message)(
                user=self.user,
                message_id=message_id
            )

            # Broadcast to group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'message_deleted',
                    'message_id': message_id
                }
            )
        except Exception as e:
            await self.send_json({
                'type': 'error',
                'message': str(e)
            })

    async def new_message(self, event):
        """
        Handle new message broadcast from group.
        """
        await self.send_json({
            'type': 'new_message',
            'message': event['message']
        })

    async def message_updated(self, event):
        """
        Handle message update broadcast from group.
        """
        await self.send_json({
            'type': 'message_updated',
            'message': event['message']
        })

    async def message_deleted(self, event):
        """
        Handle message deletion broadcast from group.
        """
        await self.send_json({
            'type': 'message_deleted',
            'message_id': event['message_id']
        })

    async def online_count(self, event):
        """
        Handle online count broadcast from group.
        """
        await self.send_json({
            'type': 'online_count',
            'count': event['count']
        })

    async def broadcast_online_count(self):
        """
        Broadcast the current online user count to the group.
        """
        count = len(_online_users.get(self.group_id, set()))
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'online_count',
                'count': count
            }
        )

    @database_sync_to_async
    def check_group_exists(self):
        """
        Check if the chat group exists.
        """
        try:
            ChatGroup.objects.get(id=self.group_id, is_active=True)
            return True
        except ChatGroup.DoesNotExist:
            return False

    @database_sync_to_async
    def get_group(self):
        """
        Get the chat group.
        """
        try:
            return ChatGroup.objects.get(id=self.group_id, is_active=True)
        except ChatGroup.DoesNotExist:
            return None

    async def check_rate_limit(self):
        """
        Check if user has exceeded rate limit.
        """
        rate_limit = getattr(settings, 'CHAT_RATE_LIMIT', 20)
        rate_limit_window = 10  # seconds

        current_time = asyncio.get_event_loop().time()
        
        # Remove timestamps older than the window
        self.rate_limit_timestamps = [
            ts for ts in self.rate_limit_timestamps
            if current_time - ts < rate_limit_window
        ]

        # Check if limit exceeded
        if len(self.rate_limit_timestamps) >= rate_limit:
            return False

        # Add current timestamp
        self.rate_limit_timestamps.append(current_time)
        return True
