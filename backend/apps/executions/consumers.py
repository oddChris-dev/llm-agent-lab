"""
WebSocket consumers for real-time execution updates.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ExecutionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time execution updates.

    Sends updates when:
    - Execution status changes
    - Node execution status changes
    - New log entries are created
    """

    async def connect(self):
        self.execution_id = self.scope['url_route']['kwargs']['execution_id']
        self.room_group_name = f'execution_{self.execution_id}'

        # Join execution group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial status
        await self.send_execution_status()

    async def disconnect(self, close_code):
        # Leave execution group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Handle incoming messages (e.g., subscription preferences).
        """
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    async def execution_update(self, event):
        """
        Handle execution status update.
        """
        await self.send(text_data=json.dumps({
            'type': 'execution_update',
            'data': event['data']
        }))

    async def node_update(self, event):
        """
        Handle node execution update.
        """
        await self.send(text_data=json.dumps({
            'type': 'node_update',
            'data': event['data']
        }))

    async def log_entry(self, event):
        """
        Handle new log entry.
        """
        await self.send(text_data=json.dumps({
            'type': 'log',
            'data': event['data']
        }))

    @database_sync_to_async
    def get_execution(self):
        from .models import Execution
        return Execution.objects.get(id=self.execution_id)

    async def send_execution_status(self):
        """
        Send current execution status.
        """
        try:
            execution = await self.get_execution()
            await self.send(text_data=json.dumps({
                'type': 'execution_update',
                'data': {
                    'status': execution.status,
                    'progress': {
                        'total_nodes': execution.total_nodes,
                        'completed_nodes': execution.completed_nodes,
                        'failed_nodes': execution.failed_nodes,
                    }
                }
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'data': {'message': str(e)}
            }))
