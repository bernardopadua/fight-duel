from random import randint
from dataclasses import asdict

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from mmo.services.fight_engine import FightEngine

@shared_task
def monsterAttack(fightId: int, channelName: str) -> None:
    if not FightEngine.isFightStillActive(fightId):
        return
    
    fs = FightEngine.attackPlayer(fightId)
    if fs is None:
        return
    
    cl = get_channel_layer()
    if cl is None: #pyright
        raise Exception("Channel layer not found")
    async_to_sync(cl.send)(channelName, {
        "type": "fight.update",
        "data": asdict(fs)
    })

    if fs.isFightOver:
        return

    monsterAttack.apply_async(args=[fightId, channelName], countdown=randint(2, 3))
