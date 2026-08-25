from dataclasses import asdict

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from mmo.services.fight_engine import FightEngine
from mmo.services.player_engine import PlayerEngine

from mmo.services.constants import MONSTER_LIFE_VARIATION, MONSTER_BASE_LIFE
from mmo.models import WorldCreature, World, Player
from mmo.data.monster_names import MONSTER_NAMES

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
        if cw.count() < i.worldTotalCreatures:
            diff = i.worldTotalCreatures - cw.count()
            for _ in range(diff):
                creatureName = random.choice(MONSTER_NAMES)
                creatureLevel = random.randint(i.worldMinLevel, i.worldMaxLevel)
                chanceDrop = int((creatureLevel*100)/i.worldMaxLevel)
                creatureLife = int(MONSTER_BASE_LIFE + (creatureLevel * MONSTER_LIFE_VARIATION))
                WorldCreature.objects.create(
                    world=i,
                    creatureName=creatureName,
                    creatureLevel=creatureLevel,
                    creatureChanceDrop=chanceDrop,
                    creatureLife=creatureLife
                )

@shared_task
def recoverPlayerStatus():
    """
        I know that this is can be better with a better control of it.
        But for a small project it fits well, I will maintain this for now.
    """
    players = Player.objects.select_related(
        "playerEquipedWeapon",
        "playerEquipedArmour"
    ).exclude(
        playerStatus__in=["dead", "fighting"]
    ).all()

    if len(players) > 0:
        PlayerEngine.recoverPlayersStatus(players)

@shared_task
def tick():
    respawnCreatures.delay()
    recoverPlayerStatus.delay()
