from asgiref.sync import async_to_sync

from dataclasses import dataclass

from django.db.models import QuerySet, F
from django.db.models.functions import Least
from django.core.cache import cache

from channels.layers import get_channel_layer


from mmo.models import Player
from mmo.services.constants import (
    PLAYER_BASE_LIFE, PLAYER_LIFE_LINEAR_POWER,
    PLAYER_TOTAL_STAMINA, PLAYER_LIFE_TOTAL_POWER_REGEN,
    LEVELUP_VARIATION_POWER, LEVELUP_MULTIPLIER_EXP,
    LEVELUP_PLUS_PLAYERPOWER, LEVEL_MAX
)
from mmo.constants import (
    USER_CHANNEL_WS_LOGGED,
)

import logging

logger = logging.getLogger(__name__)

@dataclass
class PlayerInfo:
    is_player_alive: bool
    player_id: int

class PlayerEngine:
    @staticmethod
    def get_player_id(user_id: int) -> PlayerInfo | None:
        player = Player.objects.filter(
            user_id=user_id
        ).first()

        if player is None:
            return None
        
        ps = PlayerInfo(
            is_player_alive=player.player_status != Player.PlayerStatus.DEAD,
            player_id=player.id
        )

        return ps
    
    @staticmethod
    def get_player_total_power(player: Player) -> int:
        if not player:
            raise Exception("Player not found")

        weapon = player.player_equipped_weapon.item if player.player_equipped_weapon else None
        armour = player.player_equipped_armour.item if player.player_equipped_armour else None
        wp = weapon.item_power if weapon else 0
        ap = armour.item_power if armour else 0
        items_power = wp + ap
        total_power = (player.player_power + items_power)

        return total_power

    @staticmethod
    def get_player_defense_power(player: Player) -> int:
        armour = player.player_equipped_armour.item if player.player_equipped_armour else None
        return armour.item_power if armour else 0
    
    @classmethod
    def get_player_calculated_life(cls, player: Player) -> int:
        total_power = cls.get_player_total_power(player)
        
        return int(PLAYER_BASE_LIFE + (total_power * PLAYER_LIFE_LINEAR_POWER))

    @staticmethod
    def get_player_calculated_stamina(player: Player) -> int:
        if not player:
            raise Exception("Player not found")

        return PLAYER_TOTAL_STAMINA

    @staticmethod
    def recover_players_status(players: QuerySet[Player, Player]) -> None:
        if not players:
            raise Exception("Player not found")

        for player in players:
            total_power = PlayerEngine.get_player_total_power(player)
            percent_life_restore = int((total_power * PLAYER_LIFE_TOTAL_POWER_REGEN) + 5)

            Player.objects.filter(
                id=player.id
            ).exclude(
                player_status=Player.PlayerStatus.DEAD
            ).update(
                player_stamina=Least(F('player_stamina') + (F('player_max_stamina') * (total_power / 100)), F('player_max_stamina')),
                player_life=Least(F('player_life') + percent_life_restore, F('player_max_life'))
            )

    @staticmethod
    def required_exp(player: Player) -> int:
        if not player:
            raise Exception("Player not found")

        return int(100 * (player.player_level ** LEVELUP_VARIATION_POWER))

    @classmethod
    def level_up(cls, player: Player, creature_level: int) -> None:
        if not player:
            raise Exception("Player not found")

        exp_earned = int(creature_level * LEVELUP_MULTIPLIER_EXP)
        if player.player_exp + exp_earned >= cls.required_exp(player) \
            and (player.player_level + 1) <= LEVEL_MAX:
            player.player_level += 1
            player.player_exp = 0
            player.player_power += LEVELUP_PLUS_PLAYERPOWER
            max_life = cls.get_player_calculated_life(player)
            player.player_life = max_life
            player.player_max_life = max_life
            max_stamina = cls.get_player_calculated_stamina(player)
            player.player_stamina = max_stamina
            player.player_max_stamina = max_stamina
            player.save(update_fields=[
                'player_level', 'player_exp', 
                'player_life', 'player_stamina', 
                'player_power', 'player_max_life', 'player_max_stamina'
            ])
        elif player.player_level < LEVEL_MAX:
            player.player_exp += exp_earned
            player.save(update_fields=['player_exp'])

    @staticmethod
    def player_dead_penalty(player: Player | None) -> None:
        if not player:
            logger.warning("Player not found")
            return

        armour = player.player_equipped_armour.item if player.player_equipped_armour else None
        weapon = player.player_equipped_weapon.item if player.player_equipped_weapon else None

        if armour:
            armour.delete()
            player.player_equipped_armour = None
        if weapon:
            weapon.delete()
            player.player_equipped_weapon = None

        player.player_exp = 0
        player.save(update_fields=["player_exp"])

    @staticmethod
    def revive_dead_player(player: Player | None) -> None:
        if not player:
            logger.warning("Player not found")
            return

        player.player_status = Player.PlayerStatus.IDLE
        player.save(update_fields=["player_status"])

        player_channel = cache.get(
            USER_CHANNEL_WS_LOGGED.format(user_id=player.user_id)
        )

        cl = get_channel_layer()
        if cl is None:
            logger.error("Channel layer not found")
            return

        async_to_sync(cl.send)(player_channel, {
            "type": "player.revive.notify",
            "data": {}
        })
