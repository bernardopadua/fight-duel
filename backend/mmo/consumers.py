from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from mmo.services.fight_engine import FightEngine
from mmo.services.player_engine import PlayerEngine
from mmo.services.player_inventory_engine import PlayerInventoryEngine
from mmo.tasks import monsterAttack

from random import randint
from dataclasses import asdict
import json

class ToClientActions:
    FIGHT = "fight"
    FIGHT_UPDATE = "fight.update"
    FIGHT_DROP_ITEMS = "fight.drop.items"
    FIGHT_FINISH = "fight.finish"
    INVENTORY_UPDATE = "inventory.update"

class ToServerActions:
    MOVE = "move"
    ATTACK = "attack"
    FLEE = "flee"
    LOOT = "loot"
    USE_ITEM = "use.item"

class FkingDuelConsumer(AsyncWebsocketConsumer):
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

        if data.get("action") == ToServerActions.MOVE:
            if (fs := await sync_to_async(FightEngine.shouldIFight)(self.playerId)) and fs:
                self.fightId = fs.fightId
                await self.send(json.dumps({
                    "action": ToClientActions.FIGHT,
                    "data": asdict(fs)
                }))
                await self.fight_create_group(fs.fightId)
                interval = await sync_to_async(FightEngine.monsterAttackInterval)(fs.creatureLevel)
                monsterAttack.apply_async(
                    args=[fs.fightId, self.channel_name], 
                    countdown=interval
                )
        elif data.get("action") == ToServerActions.ATTACK:
            if not self.fightId:
                return
            fs = await sync_to_async(FightEngine.attackMonster)(self.fightId)
            if fs is None: #pyright
                return

            await self.send(json.dumps({
                "action": ToClientActions.FIGHT_UPDATE,
                "data": asdict(fs)
            }))
        elif data.get("action") == ToServerActions.FLEE:
            if not self.fightId:
                return
            await sync_to_async(FightEngine.playerFlee)(self.fightId)
        elif data.get("action") == ToServerActions.LOOT:
            itemsLooted = data.get("data") or None
            if not itemsLooted:
                return
            if not isinstance(itemsLooted, list):
                return
            if not await sync_to_async(PlayerInventoryEngine.lootItems)(self.playerId, itemsLooted):
                return
            await self.send(json.dumps({
                "action": ToClientActions.INVENTORY_UPDATE,
                "data": await sync_to_async(PlayerInventoryEngine.getPlayerInventory)(self.playerId)
            }))
        elif data.get("action") == ToServerActions.USE_ITEM:
            itemId = data.get("data") or None
            if itemId is None:
                return
        elif data.get("action") == "testing":
            await sync_to_async(PlayerInventoryEngine.testing)()

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

        if itd := event.get("itemsDrop"):
            await self.send(json.dumps({
                "action": ToClientActions.FIGHT_DROP_ITEMS,
                "data": itd
            }))

        if fs := event.get("fightStatus"):
            await self.send(json.dumps({
                "action": ToClientActions.FIGHT_FINISH,
                "data": fs
            }))

    async def fight_update(self, event: dict):
        data = event["data"]
        await self.send(json.dumps({
            "action": ToClientActions.FIGHT_UPDATE,
            "data": data
        }))
