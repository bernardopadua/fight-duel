from mmo.models import Player

class PlayerEngine:
    @staticmethod
    def getPlayerId(userId: int) -> int | None:
        player = Player.objects.filter(
            user_id=userId
        ).first()

        if player is None:
            return None
        
        return player.id
