from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from django.core.cache import cache

from mmo.services.fight_engine import FightEngine
from mmo.services.player_engine import PlayerEngine
from mmo.services.player_inventory_engine import PlayerInventoryEngine
from mmo.tasks import monster_attack
from mmo.constants import USER_CHANNEL_WS_LOGGED

from typing import override
import json

class ToClientActions:
    ERROR = "error"

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
    GET_INVENTORY = "get.inventory"

class FightDuelConsumer(AsyncWebsocketConsumer):
    
    @override
    async def connect(self) -> None:
        self.fight_id = None

        if not "user" in self.scope or self.scope["user"] is None:
            await self.close()
            return
        
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return
        
        player_id = await sync_to_async(PlayerEngine.get_player_id)(self.user.id)
        if player_id is None:
            await self.close()
            return

        self.player_id = player_id

        if not await cache.aadd(
            USER_CHANNEL_WS_LOGGED.format(user_id=self.user.id),
            self.channel_name
        ):
            await self.close()
            return

        await self.accept()

    @override
    async def disconnect(self, code: int) -> None:
        if self.fight_id:
            await sync_to_async(FightEngine.player_flee)(self.fight_id)
            await self.fight_finish_group({"fightId": self.fight_id})

        user = self.scope.get('user')
        if user and not user.is_anonymous:
            key = USER_CHANNEL_WS_LOGGED.format(user_id=user.id)
            if await cache.aget(key) == self.channel_name:
                await cache.adelete(key)

    async def user_logout(self, event: dict) -> None:
        await self.close(1000)

    @override
    async def receive(self, text_data=None, bytes_data=None) -> None:
        if text_data is None:
            return
       
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({
                "action": ToClientActions.ERROR,
                "data": "Invalid JSON"
            }))
            await self.close()
            return

        if data.get("action") == ToServerActions.MOVE:
            if (fs := await sync_to_async(FightEngine.should_fight)(self.player_id)) and fs:
                self.fight_id = fs.fight_id
                await self.fight_create_group(fs.fight_id)
                interval = await sync_to_async(FightEngine.monster_attack_interval)(fs.creature_level)
                monster_attack.apply_async(
                    args=[fs.fight_id, self.channel_name], 
                    countdown=interval
                )
                await self.send(json.dumps({
                    "action": ToClientActions.FIGHT,
                    "data": fs.to_dict()
                }))
        elif data.get("action") == ToServerActions.ATTACK:
            if not self.fight_id:
                return
            fs = await sync_to_async(FightEngine.attack_monster)(self.fight_id)
            if fs is None: #pyright
                return

            await self.send(json.dumps({
                "action": ToClientActions.FIGHT_UPDATE,
                "data": fs.to_dict()
            }))
        elif data.get("action") == ToServerActions.FLEE:
            if not self.fight_id:
                return
            await sync_to_async(FightEngine.player_flee)(self.fight_id)
        elif data.get("action") == ToServerActions.LOOT:
            items_looted = data.get("data") or None
            if not items_looted:
                return
            if not isinstance(items_looted, list):
                return
            if not await sync_to_async(PlayerInventoryEngine.loot_items)(self.player_id, items_looted):
                return
            await self.send(json.dumps({
                "action": ToClientActions.INVENTORY_UPDATE,
                "data": await sync_to_async(PlayerInventoryEngine.get_player_inventory)(self.player_id)
            }))
        elif data.get("action") == ToServerActions.USE_ITEM:
            item_id = data.get("data") or None
            if item_id is None:
                return
            if not await sync_to_async(PlayerInventoryEngine.use_item)(self.player_id, item_id):
                return
            await self.send(json.dumps({
                "action": ToClientActions.INVENTORY_UPDATE,
                "data": await sync_to_async(PlayerInventoryEngine.get_player_inventory)(self.player_id)
            }))
        elif data.get("action") == ToServerActions.GET_INVENTORY:
            await self.send(json.dumps({
                "action": ToClientActions.INVENTORY_UPDATE,
                "data": await sync_to_async(PlayerInventoryEngine.get_player_inventory)(self.player_id)
            }))

    async def fight_create_group(self, fight_id: int) -> None:
        await self.channel_layer.group_add(
            f"fight_{fight_id}",
            self.channel_name
        )

    async def fight_finish_group(self, event: dict) -> None:
        await self.channel_layer.group_discard(
            f"fight_{event['fightId']}",
            self.channel_name
        )

        self.fight_id = None

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

    async def fight_update(self, event: dict) -> None:
        data = event["data"]
        await self.send(json.dumps({
            "action": ToClientActions.FIGHT_UPDATE,
            "data": data
        }))
