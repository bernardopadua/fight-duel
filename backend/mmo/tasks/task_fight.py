from celery import shared_task

from mmo.services.fight_engine import FightEngine

@shared_task
def monster_attack(fight_id: int, channel_name: str) -> None:
    if not FightEngine.is_fight_still_active(fight_id):
        return
    
    fs = FightEngine.attack_player(fight_id)
    if fs is None: #pyright
        return

    if fs.is_fight_over:
        return

    if fs.creature_level is None:
        return

    monster_attack.apply_async(args=[fight_id, channel_name], countdown=fs.is_creature_attacking)
