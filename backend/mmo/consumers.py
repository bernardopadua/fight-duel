from channels.generic.websocket import AsyncWebsocketConsumer

class FightConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return
        await self.accept()