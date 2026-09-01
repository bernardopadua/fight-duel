from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer

from django.core.cache import cache

from mmo.models import Fight, Player
from mmo.constants import (
    USER_CHANNEL_WS_LOGGED, FIGHT_GROUP, 
    OPPONENTS_IN_FIGHT_CACHE, MATCHMAKING_IN_FIGHT
)
from mmo.services.fight_engine import FightEngine

import logging

logger = logging.getLogger('matchmaking_engine')

class MatchmakingEngine:
    @staticmethod
    def inform_player_matchmaking(fight_id: int, challenger_name: str, challenger_level: int) -> bool:
        f = Fight.objects.filter(id=fight_id).select_related(
            'opponent',
            'player'
        ).first()
        if not f:
            return False

        p: Player = f.player
        o: Player = f.opponent

        if not p or not o:
            logger.error('No player or opponent for fight %s', fight_id)
            return False

        # CACHE
        cache.set(
            OPPONENTS_IN_FIGHT_CACHE.format(fight_id=fight_id),
            {
                "opponents":[
                    {
                        "playerName": p.player_name,
                        "playerLevel": p.player_level,
                    },
                    {
                        "playerName": o.player_name,
                        "playerLevel": o.player_level,
                    }
                ]
            },
            timeout=120
        )

        cl = get_channel_layer()
        opponent_ch = cache.get(
            USER_CHANNEL_WS_LOGGED.format(user_id=o.user_id)
        )

        if not opponent_ch:
            return False
        
        async_to_sync(cl.send)(
            opponent_ch,
            {
                "type": "fight.matchmaking",
                "data": {
                    "fightId": fight_id,
                    "challengerName": challenger_name,
                    "challengerLevel": challenger_level
                }
            }
        )

        return True

    @staticmethod
    def inform_group_matchmaking_accepted(fight_id: int) -> bool:
        f = Fight.objects.filter(
            id=fight_id
        ).exists()
        if not f:
            return False

        opponents = cache.get(OPPONENTS_IN_FIGHT_CACHE.format(fight_id=fight_id))
        if not opponents:
            logger.error('No opponents for fight %s', fight_id)
            return False

        cl = get_channel_layer()
        if not cl:
            logger.error('No channel layer for fight %s', fight_id)
            return False

        async_to_sync(cl.group_send)(
            FIGHT_GROUP.format(fight_id=fight_id),
            {
                "type": "fight.matchmaking.accepted",
                "data": {
                    "fightId": fight_id,
                    "opponents": opponents
                }
            }
        )

        return True

    @staticmethod
    def inform_group_matchmaking_rejected(fight_id: int, player_id: int) -> bool:
        cl = get_channel_layer()
        if not cl:
            logger.error('No channel layer for fight %s', fight_id)
            return False

        async_to_sync(cl.group_send)(
            FIGHT_GROUP.format(fight_id=fight_id),
            {
                "type": "fight.matchmaking.rejected",
                "data": {
                    "fightId": fight_id
                }
            }
        )

        FightEngine.unlock_finish_fight_pvp(fight_id, player_id, None)

        return True  

    @staticmethod
    def matchmaking_in_fight(fight_id: int) -> bool:
        # after accept the fight players have 2 minutes to start the fight
        f = cache.set(
            MATCHMAKING_IN_FIGHT.format(fight_id=fight_id),
            True,
            timeout=120
        )
        if not f:
            return False
        return True

    @staticmethod
    def matchmaking_cleanup_task_run(fight_id: int) -> None:
        from mmo.tasks.task_matchmaking import clean_up_matchmaking_fight
        clean_up_matchmaking_fight.apply_async(args=[fight_id], countdown=60)

    @staticmethod
    def matchmaking_timeout(fight_id: int) -> bool:
        f = Fight.objects.filter(
            id=fight_id,
        ).first()
        if not f:
            logger.error('[matchmaking_timeout]: No fight for fight %s', fight_id)
            return False

        cl = get_channel_layer()
        if not cl:
            logger.error('[matchmaking_timeout]: No channel layer for fight %s', fight_id)
            return False

        async_to_sync(cl.group_send)(
            FIGHT_GROUP.format(fight_id=fight_id),
            {
                "type": "fight.matchmaking.timeout",
                "data": {
                    "fightId": fight_id
                }
            }
        )
        
        FightEngine.unlock_finish_fight_pvp(fight_id, f.player_id, None)        

        return True
