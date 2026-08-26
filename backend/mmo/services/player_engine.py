from django.db.models import QuerySet
from mmo.models import Player
from mmo.services.constants import (
    PLAYER_BASE_LIFE, PLAYER_LIFE_LINEAR_POWER,
    PLAYER_TOTAL_STAMINA, PLAYER_LIFE_TOTAL_POWER_REGEN,
    LEVELUP_VARIATION_POWER, LEVELUP_MULTIPLIER_EXP,
    LEVELUP_PLUS_PLAYERPOWER, MAX_PLAYER_LEVEL
)

class PlayerEngine:
    @staticmethod
    def get_player_id(user_id: int) -> int | None:
        player = Player.objects.filter(
            user_id=user_id
        ).first()

        if player is None:
            return None
        
        return player.id
    
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
            player_total_life = PlayerEngine.get_player_calculated_life(player)

            if player.player_stamina < PLAYER_TOTAL_STAMINA:
                player.player_stamina = min(
                    PLAYER_TOTAL_STAMINA,
                    int(player.player_stamina + (PlayerEngine.get_player_calculated_stamina(player) * (total_power / 100)))
                )
            if player.player_life < player_total_life:
                percent_life_restore = int((total_power * PLAYER_LIFE_TOTAL_POWER_REGEN) + 5)
                player.player_life = min(player_total_life, player.player_life + percent_life_restore)

            player.save(update_fields=["player_life", "player_stamina"])

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
            and (player.player_level + 1) <= MAX_PLAYER_LEVEL:
            player.player_level += 1
            player.player_exp = 0
            player.player_power += LEVELUP_PLUS_PLAYERPOWER
            player.player_life = cls.get_player_calculated_life(player)
            player.player_stamina = cls.get_player_calculated_stamina(player)
            player.save(update_fields=[
                "player_level", "player_exp", 
                "player_life", "player_stamina", 
                "player_power"
            ])
        elif player.player_level < MAX_PLAYER_LEVEL:
            player.player_exp += exp_earned
            player.save(update_fields=["player_exp"])

    @staticmethod
    def player_dead_penalty(player: Player) -> None:
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
