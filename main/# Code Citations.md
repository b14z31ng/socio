# Code Citations

## License: unknown
https://github.com/sudhinsr/django-channels-sample/tree/67beddf159dd545eb102450c3e98f54b8a114f69/tutorial/quickstart/consumer.py

```
channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        await self.channel_layer
```

