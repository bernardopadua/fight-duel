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
    def getPlayerId(userId: int) -> int | None:
        player = Player.objects.filter(
            user_id=userId
        ).first()

        if player is None:
            return None
        
        return player.id
    
    @staticmethod
    def getPlayerTotalPower(player: Player) -> int:
        if not player:
            raise Exception("Player not found")

        weapon = player.player_equipped_weapon.item if player.player_equipped_weapon else None
        armour = player.player_equipped_armour.item if player.player_equipped_armour else None
        wp = weapon.item_power if weapon else 0
        ap = armour.item_power if armour else 0
        itemsPower = wp + ap
        totalPower = (player.player_power + itemsPower)

        return totalPower
    
    @classmethod
    def getPlayerCalulatedLife(cls, player: Player) -> int:
        totalPower = cls.getPlayerTotalPower(player)
        
        return int(PLAYER_BASE_LIFE+(totalPower*PLAYER_LIFE_LINEAR_POWER))

    @staticmethod
    def getPlayerCalulatedStamina(player: Player) -> int:
        if not player:
            raise Exception("Player not found")

        return PLAYER_TOTAL_STAMINA

    @staticmethod
    def recoverPlayersStatus(players: QuerySet[Player, Player]) -> None:
        if not players:
            raise Exception("Player not found")

        for player in players:
            totalPower = PlayerEngine.getPlayerTotalPower(player)
            playerTotalLife = PlayerEngine.getPlayerCalulatedLife(player)

            if player.player_stamina < PLAYER_TOTAL_STAMINA:
                player.player_stamina = min(
                    PLAYER_TOTAL_STAMINA,
                    int(player.player_stamina + (PlayerEngine.getPlayerCalulatedStamina(player)*(totalPower/100)))
                )
            if player.player_life < playerTotalLife:
                percentLifeRestore = int((totalPower * PLAYER_LIFE_TOTAL_POWER_REGEN) + 5)
                player.player_life = min(playerTotalLife, player.player_life + percentLifeRestore)

            player.save(update_fields=["player_life", "player_stamina"])

    @staticmethod
    def requiredExp(player: Player) -> int:
        if not player:
            raise Exception("Player not found")

        return int(100*(player.player_level**LEVELUP_VARIATION_POWER))

    @classmethod
    def levelUp(cls, player: Player, creatureLevel: int):
        if not player:
            raise Exception("Player not found")

        expEarned = int(creatureLevel * LEVELUP_MULTIPLIER_EXP)
        if player.player_exp + expEarned >= cls.requiredExp(player) \
            and (player.player_level+1) <= MAX_PLAYER_LEVEL:
            player.player_level += 1
            player.player_exp = 0
            player.player_power += LEVELUP_PLUS_PLAYERPOWER
            player.player_life = cls.getPlayerCalulatedLife(player)
            player.player_stamina = cls.getPlayerCalulatedStamina(player)
            player.save(update_fields=[
                "player_level", "player_exp", 
                "player_life", "player_stamina", 
                "player_power"
            ])
        elif player.player_level < MAX_PLAYER_LEVEL:
            player.player_exp += expEarned
            player.save(update_fields=["player_exp"])

