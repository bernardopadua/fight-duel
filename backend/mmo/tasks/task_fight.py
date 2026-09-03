from asgiref.sync import async_to_sync
from celery import shared_task

from channels.layers import get_channel_layer

from mmo.services.fight_engine import FightEngine

@shared_task
def monster_attack(fight_id: int, channel_name: str) -> None:
    if not FightEngine.is_fight_still_active(fight_id):
        return
    
    fs = FightEngine.attack_player(fight_id)
    if fs is None: #pyright
        return

    cl = get_channel_layer()
    if cl is None: #pyright
        raise Exception("Channel layer not found")
    async_to_sync(cl.send)(channel_name, {
        "type": "fight.update",
        "data": fs.to_dict()
    })

    if fs.is_fight_over:
        return

    if fs.creature_level is None:
        return
    
    monster_attack.apply_async(args=[fight_id, channel_name], countdown=fs.is_creature_attacking)
