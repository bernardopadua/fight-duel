from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from mmo.services.fight_engine import FightEngine
from mmo.services.player_engine import PlayerEngine
from mmo.tasks import monsterAttack

from random import randint
from dataclasses import asdict
import json

class FightConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not "user" in self.scope or self.scope["user"] is None:
            await self.close()
            return
        
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
        
        playerId = await sync_to_async(PlayerEngine.getPlayerId)(self.user.id)
        if playerId is None:
            await self.close()
            return

        self.playerId = playerId
        self.fightId = None

        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            return
       
        data = json.loads(text_data)

        if data.get("action") == "move":
            if (fs := await sync_to_async(FightEngine.shouldIFight)(self.playerId)) and fs:
                self.fightId = fs.fightId
                await self.send(json.dumps({
                    "action": "fight",
                    "data": asdict(fs)
                }))
                await self.fight_create_group(fs.fightId)
                monsterAttack.apply_async(
                    args=[fs.fightId, self.channel_name], 
                    countdown=randint(2, 3)
                )
        elif data.get("action") == "attack":
            if not self.fightId:
                return
            fs = await sync_to_async(FightEngine.attackMonster)(self.fightId)
            if fs is None: #pyright
                return

            await self.send(json.dumps({
                "action": "fight.update",
                "data": asdict(fs)
            }))
    
    async def fight_create_group(self, fightId: int):
        await self.channel_layer.group_add(
            f"fight_{fightId}",
            self.channel_name
        )

    async def fight_finish_group(self, event: dict):
        await self.channel_layer.group_discard(
            f"fight_{event["fightId"]}",
            self.channel_name
        )

        self.fightId = None

    async def fight_update(self, event: dict):
        data = event["data"]
        await self.send(json.dumps({
            "action": "fight.update",
            "data": data
        }))
