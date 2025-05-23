import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = self.room_name
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if 'message' in data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': data['message']
                }
            )
        if 'typing' in data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'typing': data['typing'],
                    'sender': data['sender']
                }
            )
        if 'read' in data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'read': True,
                    'sender': data['sender']
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({'message': event['message']}))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({'typing': event['typing'], 'sender': event['sender']}))

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({'read': event['read'], 'sender': event['sender']}))

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'call_{self.room_name}'
        print(f'[CallConsumer] connect: user channel={self.channel_name}, room_name={self.room_name}, group={self.room_group_name}')
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        print(f'[CallConsumer] disconnect: user channel={self.channel_name}, group={self.room_group_name}')
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        print(f'[CallConsumer] receive: from channel={self.channel_name}, group={self.room_group_name}, data={text_data}')
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'signal_message',
                'message': text_data,
                'sender_channel_name': self.channel_name
            }
        )

    async def signal_message(self, event):
        print(f'[CallConsumer] signal_message: to channel={self.channel_name}, sender_channel={event.get("sender_channel_name")}, group={self.room_group_name}')
        if self.channel_name != event.get('sender_channel_name'):
            await self.send(text_data=event['message'])
