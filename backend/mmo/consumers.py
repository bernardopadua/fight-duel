from re import Match

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from django.core.cache import cache

from mmo.services.fight_engine import FightEngine, FightStart
from mmo.services.player_engine import PlayerEngine
from mmo.services.player_inventory_engine import PlayerInventoryEngine
from mmo.services.world_engine import WorldEngine
from mmo.services.matchmaking_engine import MatchmakingEngine
from mmo.tasks.task_fight import monster_attack
from mmo.constants import USER_CHANNEL_WS_LOGGED, FIGHT_GROUP

from typing import override
from opentelemetry import trace
import json, logging

logger = logging.getLogger("fight_duel_consumer")
tracer = trace.get_tracer(__name__)

class ToClientActions:
    ERROR = "error"
    
    WORLD_ENTER = "world.enter"

    FIGHT_MATCHMAKING = "fight.matchmaking"
    FIGHT_MATCHMAKING_START = "fight.matchmaking.start"
    FIGHT_MATCHMAKING_REJECT = "fight.matchmaking.reject"
    FIGHT_MATCHMAKING_TIMEOUT = "fight.matchmaking.timeout"

    FIGHT = "fight"
    FIGHT_UPDATE = "fight.update"
    FIGHT_DROP_ITEMS = "fight.drop.items"
    FIGHT_FINISH = "fight.finish"
    INVENTORY_UPDATE = "inventory.update"

    PLAYER_REVIVE = "player.revive"

class ToServerActions:
    ENTER_WORLD = "enter.world"
    LEAVE_WORLD = "leave.world"
    CHANGE_WORLD = "change.world"

    ACCEPT_MATCHMAKING = "accept.matchmaking"
    REJECT_MATCHMAKING = "reject.matchmaking"

    MOVE = "move"
    ATTACK = "attack"
    FLEE = "flee"
    LOOT = "loot"
    USE_ITEM = "use.item"
    GET_INVENTORY = "get.inventory"

class FightDuelConsumer(AsyncWebsocketConsumer):
    
    @override
    async def connect(self) -> None:
        with tracer.start_as_current_span('ws connect'):
            await self._on_connect()

    @override
    async def disconnect(self, code: int) -> None:
        with tracer.start_as_current_span('ws disconnect') as span:
            span.set_attribute('ws.code', code)
            await self._on_disconnect()

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

        action = data.get('action')
        with tracer.start_as_current_span(f'ws {action or 'unknown'}') as span:
            span.set_attribute('ws.action', action or 'unknown')
            if self.player_id:
                span.set_attribute('player.id', self.player_id)
            if self.fight_id:
                span.set_attribute('fight.id', self.fight_id)
            span.set_attribute('fight.matchmaking', self.matchmaking)
            span.set_attribute('fight.pvp', self.pvp)

            await self._on_action(data)

    async def _on_connect(self):
        self.fight_id = None
        self.matchmaking = False
        self.pvp = False
        self.player_id = 0
        self.player_is_alive = False

        if not "user" in self.scope or self.scope["user"] is None:
            await self.close()
            return
        
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return
        
        player_info = await sync_to_async(PlayerEngine.get_player_id)(self.user.id)
        if player_info is None:
            await self.close()
            return

        self.player_id = player_info.player_id
        self.player_is_alive = player_info.is_player_alive

        if not await cache.aadd(
            USER_CHANNEL_WS_LOGGED.format(user_id=self.user.id),
            self.channel_name,
            timeout=None
        ):
            await self.close()
            return

        await self.accept()

    async def _on_disconnect(self):
        if self.player_id and self.fight_id:
            is_pvp = self.matchmaking or self.pvp
            await sync_to_async(FightEngine.player_flee)(self.fight_id, self.player_id, is_pvp=is_pvp)

        if self.player_id:
            #if player is in a world, leave it
            await sync_to_async(WorldEngine.leave_world)(self.player_id)

        user = self.scope.get('user')
        if user and not user.is_anonymous:
            key = USER_CHANNEL_WS_LOGGED.format(user_id=user.id)
            if await cache.aget(key) == self.channel_name:
                await cache.adelete(key)

    async def _on_action(self, data: dict) -> None:
        if self.matchmaking and \
            data.get("action") != ToServerActions.ACCEPT_MATCHMAKING and \
            data.get("action") != ToServerActions.REJECT_MATCHMAKING \
        :
            logger.error("Player %s is matchmaking but received action %s", self.user.id, data.get("action"))
            return

        if not self.player_is_alive:
            await self.send(json.dumps({
                "action": ToClientActions.ERROR,
                "data": "Player is dead, please wait for revival"
            }))
            return

        if data.get("action") == ToServerActions.ENTER_WORLD:
            world_id = data.get("data") or None
            if not world_id:
                return
            if world := await sync_to_async(WorldEngine.enter_world)(self.player_id, world_id):
                await self.send(json.dumps({
                    "action": ToClientActions.WORLD_ENTER,
                    "data": world.to_world_enter()
                }))
        elif data.get("action") == ToServerActions.LEAVE_WORLD:
            await sync_to_async(WorldEngine.leave_world)(self.player_id)
        elif data.get("action") == ToServerActions.CHANGE_WORLD:
            world_id = data.get("data") or None
            if not world_id:
                return
            if world := await sync_to_async(WorldEngine.enter_world)(self.player_id, world_id):
                await self.send(json.dumps({
                    "action": ToClientActions.WORLD_ENTER,
                    "data": world.to_world_enter()
                }))
        elif data.get("action") == ToServerActions.ACCEPT_MATCHMAKING:
            if not self.fight_id:
                logger.error("No fight id for user %s", self.user.id)
                return
            await sync_to_async(MatchmakingEngine.inform_group_matchmaking_accepted)(self.fight_id, self.player_id)
        elif data.get("action") == ToServerActions.REJECT_MATCHMAKING:
            if not self.fight_id:
                logger.error("No fight id for user %s", self.user.id)
                return
            await sync_to_async(MatchmakingEngine.inform_group_matchmaking_rejected)(self.fight_id, self.player_id)
        elif data.get("action") == ToServerActions.MOVE:
            if (fs := await sync_to_async(FightEngine.should_fight)(self.player_id)) and fs:
                self.fight_id = fs.fight_id
                await self.fight_create_group(fs.fight_id)
                
                if not fs.opponent:
                    await self.schedule_monster_attack(fs)

                    await self.send(json.dumps({
                        "action": ToClientActions.FIGHT,
                        "data": fs.to_dict()
                    }))
                else:
                    self.matchmaking = True
                    await sync_to_async(MatchmakingEngine.matchmaking_cleanup_task_run)(self.fight_id)
                    await sync_to_async(MatchmakingEngine.inform_player_matchmaking)(
                        self.fight_id, 
                        fs.player.player_name, 
                        fs.player.player_level
                    )

                    await self.send(json.dumps({
                        "action": ToClientActions.FIGHT_MATCHMAKING_START,
                        "data": fs.to_dict()
                    }))
        elif data.get("action") == ToServerActions.ATTACK:
            if not self.fight_id:
                return
            
            if self.pvp:
                fs, fs_o = await sync_to_async(FightEngine.attack_pvp_player)(self.fight_id, self.player_id)
                if not fs and not fs_o:
                    # It's normal, but I will maintain for now
                    logger.warning("No fight state for fight %s", self.fight_id)
                    return
                data = {}
                if fs:
                    data[fs.player_id] = fs.to_dict()
                if fs_o:
                    data[fs_o.player_id] = fs_o.to_dict()

                await self.channel_layer.group_send(
                    FIGHT_GROUP.format(fight_id=self.fight_id),
                    {
                        "type": "fight.pvp.update",
                        "data": data
                    }
                )
            else:
                fs = await sync_to_async(FightEngine.attack_monster)(self.fight_id)
                if fs:
                    await self.send(json.dumps({
                        "action": ToClientActions.FIGHT_UPDATE,
                        "data": fs.to_dict()
                    }))
        elif data.get("action") == ToServerActions.FLEE:
            if not self.fight_id:
                return
            await sync_to_async(FightEngine.player_flee)(self.fight_id, self.player_id, is_pvp=self.pvp)
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
        
    async def schedule_monster_attack(self, fs: FightStart) -> None:
        if not self.fight_id:
            return
        creature_level = fs.creature_level if fs.creature_level else None
        if not creature_level:
            logger.error("No creature level %s", fs.fight_id)
            return

        interval = await sync_to_async(FightEngine.monster_attack_interval)(creature_level)
        monster_attack.apply_async(
            args=[fs.fight_id, self.channel_name], 
            countdown=interval
        )

    async def fight_create_group(self, fight_id: int) -> None:
        await self.channel_layer.group_add(
            FIGHT_GROUP.format(fight_id=fight_id),
            self.channel_name
        )

    async def fight_finish_group(self, event: dict) -> None:
        await self.channel_layer.group_discard(
            FIGHT_GROUP.format(fight_id=event['fightId']),
            self.channel_name
        )

        self.fight_id = None
        self.matchmaking = False
        self.pvp = False

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
    
    async def fight_pvp_update(self, event: dict) -> None:
        #Send data to both players
        data = event["data"]
        if not isinstance(data, dict):
            logger.error("Invalid fight pvp update data %s", data)
            return
        for_me = data.get(self.player_id)
        if not for_me:
            logger.error("No fight state for player %s in fight %s", self.player_id, self.fight_id)
            return
        await self.send(json.dumps({
            "action": ToClientActions.FIGHT_UPDATE,
            "data": for_me
        }))

    async def fight_matchmaking(self, event: dict) -> None:
        data = event["data"]
        fight_id = data.get("fightId")
        challenger_name = data.get("challengerName")
        challenger_level = data.get("challengerLevel")
        
        self.matchmaking = True
        self.fight_id = fight_id
        
        await self.fight_create_group(fight_id)

        await self.send(json.dumps({
            "action": ToClientActions.FIGHT_MATCHMAKING,
            "data": {
                "fightId": fight_id,
                "challengerName": challenger_name,
                "challengerLevel": challenger_level
            }
        }))
    
    async def fight_matchmaking_accepted(self, event: dict) -> None:
        data = event["data"]
        fight_id = data.get("fightId")
        opponents = data.get("opponents")
        if not fight_id:
            logger.error("No fight id for user %s", self.user.id)
            return

        await sync_to_async(MatchmakingEngine.matchmaking_in_fight)(fight_id)

        self.pvp = True
        self.matchmaking = False

        await self.send(json.dumps({
            "action": ToClientActions.FIGHT,
            "data": {
                "fightId": fight_id,
                "opponents": opponents
            }
        }))

    async def fight_matchmaking_rejected(self, event: dict) -> None:
        await self.send(json.dumps({
            "action": ToClientActions.FIGHT_MATCHMAKING_REJECT,
            "data": {
                "fightId": event['data']['fightId']
            }
        }))

    async def fight_matchmaking_timeout(self, event: dict) -> None:
        await self.send(json.dumps({
            "action": ToClientActions.FIGHT_MATCHMAKING_TIMEOUT,
            "data": {
                "fightId": event['data']['fightId']
            }
        }))

    async def player_revive_notify(self, event: dict) -> None:
        self.player_is_alive = True
        await self.send(json.dumps({
            "action": ToClientActions.PLAYER_REVIVE
        }))
