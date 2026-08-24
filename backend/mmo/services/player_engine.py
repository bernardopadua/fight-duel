from django.db.models import QuerySet
from mmo.models import Player
from mmo.services.constants import (
    PLAYER_BASE_LIFE, PLAYER_LIFE_LINEAR_POWER,
    PLAYER_TOTAL_STAMINA, PLAYER_LIFE_TOTAL_POWER_REGEN
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

        wp = player.playerEquipedWeapon.itemPower if player.playerEquipedWeapon else 0
        ap = player.playerEquipedArmour.itemPower if player.playerEquipedArmour else 0
        itemsPower = wp + ap
        totalPower = (player.playerPower + itemsPower)

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

            if player.playerStamina < PLAYER_TOTAL_STAMINA:
                player.playerStamina = min(
                    PLAYER_TOTAL_STAMINA,
                    int(player.playerStamina + (PlayerEngine.getPlayerCalulatedStamina(player)*(totalPower/100)))
                )
            if player.playerLife < playerTotalLife:
                percentLifeRestore = int((totalPower * PLAYER_LIFE_TOTAL_POWER_REGEN) + 5)
                player.playerLife = min(playerTotalLife, player.playerLife + percentLifeRestore)

            player.save(update_fields=["playerLife", "playerStamina"])
