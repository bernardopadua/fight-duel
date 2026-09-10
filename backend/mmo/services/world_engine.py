from mmo.services.fight_engine import FightEngine
from mmo.models import Player, World

import logging

logger = logging.getLogger(__name__)

class WorldEngine:  

    @staticmethod
    def enter_world(player_id: int, world_id: int) -> World | None:
        world = World.objects.filter(
            id=world_id
        ).first()
        if not world:
            return None

        p = Player.objects.filter(id=player_id).first()
        if not p:
            logger.error("Player not found %s", player_id)
            return None
        
        if FightEngine.is_player_in_a_fight(player_id):
            logger.warning("Player %s is in a fight", player_id)
            return None
        
        if p.player_level > world.world_max_level or p.player_level < world.world_min_level:
            return None

        Player.objects.filter(
            id=player_id
        ).update(
            player_world_id=world_id,
        )

        return world
    
    @staticmethod
    def leave_world(player_id: int) -> bool:
        if FightEngine.is_player_in_a_fight(player_id):
            logger.warning("Player %s is in a fight", player_id)
            return False

        try:
            Player.objects.filter(
                id=player_id,
            ).exclude(
                player_world__isnull=True
            ).update(
                player_world_id=None,
            )
        except Exception as e:
            logger.error("Error leaving world: %s", e)
            return False

        return True
