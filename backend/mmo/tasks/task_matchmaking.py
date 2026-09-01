from celery import shared_task

from django.core.cache import cache

from mmo.services.matchmaking_engine import MatchmakingEngine
from mmo.constants import MATCHMAKING_IN_FIGHT

@shared_task
def clean_up_matchmaking_fight(fight_id: int) -> None:
    if cache.get(MATCHMAKING_IN_FIGHT.format(fight_id=fight_id)):
        return
    MatchmakingEngine.matchmaking_timeout(fight_id)