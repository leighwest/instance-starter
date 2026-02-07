import json
from channels.generic.websocket import AsyncWebsocketConsumer

class EC2Consumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join a group. Using one group here so that all clients receive the same updates.
        self.group_name = 'ec2_updates'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def ec2_update(self, event):
        # Retrieve the combined instances data.
        try:
            instances = event.get('instances', {})
            await self.send(text_data=json.dumps({
                'instances': instances
            }))
        except Exception as e:
            print(f"Error sending EC2 update: {e}")