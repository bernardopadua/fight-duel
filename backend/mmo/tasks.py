from dataclasses import asdict
from asgiref.sync import async_to_sync

from celery import shared_task
from channels.layers import get_channel_layer
from django.utils import timezone

from mmo.services.fight_engine import FightEngine
from mmo.services.player_engine import PlayerEngine
from mmo.services.constants import MONSTER_LIFE_VARIATION, MONSTER_BASE_LIFE

from mmo.models import WorldCreature, World, Player, Item
from mmo.data.monster_names import MONSTER_NAMES

from datetime import timedelta
import random

@shared_task
def monsterAttack(fightId: int, channelName: str) -> None:
    if not FightEngine.isFightStillActive(fightId):
        return
    
    fs = FightEngine.attackPlayer(fightId)
    if fs is None: #pyright
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

    if fs.creatureLevel is None:
        return
    
    monsterAttack.apply_async(args=[fightId, channelName], countdown=fs.isCreatureAttacking)

@shared_task
def respawnCreatures():
    w = World.objects.all()
    for i in w:
        cw = WorldCreature.objects.filter(
            world=i.id
        )
        if cw.count() < i.world_total_creatures:
            diff = i.world_total_creatures - cw.count()
            for _ in range(diff):
                creatureName = random.choice(MONSTER_NAMES)
                creatureLevel = random.randint(i.world_min_level, i.world_max_level)
                chanceDrop = int((creatureLevel*100)/i.world_max_level)
                creatureLife = int(MONSTER_BASE_LIFE + (creatureLevel * MONSTER_LIFE_VARIATION))
                WorldCreature.objects.create(
                    world=i,
                    creature_name=creatureName,
                    creature_level=creatureLevel,
                    creature_chance_drop=chanceDrop,
                    creature_life=creatureLife
                )

@shared_task
def recoverPlayerStatus():
    """
        I know that this can be better with a better control of it.
        But for a small project it fits well, I will maintain this for now.
    """
    players = Player.objects.select_related(
        "player_equipped_weapon__item",
        "player_equipped_armour__item"
    ).exclude(
        player_status__in=["dead", "fighting"]
    ).all()

    if len(players) > 0:
        PlayerEngine.recoverPlayersStatus(players)

@shared_task
def tick():
    respawnCreatures.delay()
    recoverPlayerStatus.delay()

@shared_task
def cleanOrphanItems():
    timeSince = timezone.now()-timedelta(days=1)

    orphanItems = Item.objects.filter(
        item_created_date__lte=timeSince,
        playerinventory__isnull=True
    ).all()

    if len(orphanItems) > 0:
        orphanItems.delete()
