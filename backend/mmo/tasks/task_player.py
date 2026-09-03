from celery import shared_task

from mmo.services.player_engine import PlayerEngine
from mmo.models import Player

@shared_task
def apply_death_penalty_to_player(player_id: int) -> None:
    p = Player.objects.filter(id=player_id).first()
    PlayerEngine.player_dead_penalty(p)
