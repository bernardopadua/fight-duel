from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer

from django.db import transaction

from mmo.models import Player, Fight, WorldCreature

from random import randint
from dataclasses import dataclass

@dataclass
class FightStatus:
    isPlayerAlive: bool = True
    isMonsterAlive: bool = True
    isFightOver: bool = False
    playerLife: int | None = None
    creatureLife: int | None = None

@dataclass
class FightStart:
    fightId: int
    creatureName: str
    creatureLevel: int

class FightEngine:

    @classmethod
    def shouldIFight(cls, playerId: int) -> FightStart | None:
        creatures = WorldCreature.objects.filter(
            fight__isnull=True
        ).order_by('id')
        if not creatures.exists():
            return None
        
        creature = creatures.first()
        if creature is None:
            return None

        playerIsFight = Player.objects.filter(
            fight__isnull=True,
            id=playerId
        )
        if not playerIsFight.exists():
            return None

        fight = cls.lockFight(creature.id, playerId)
        if fight is None:
            return None
        
        return FightStart(
            fightId=fight.id,
            creatureName=creature.creatureName,
            creatureLevel=creature.creatureLevel
        )
        
    @staticmethod
    def lockFight(creatureId: int, playerId: int) -> Fight | None:
        #maybe some more checking here?
        
        with transaction.atomic():
            isCreatureLocked = WorldCreature.objects.select_for_update(
                skip_locked=True
            ).filter(id=creatureId).first()

            if isCreatureLocked is None:
                #TODO: Treat with a exception here
                return

            with transaction.atomic():
                Player.objects.filter(
                    id=playerId
                ).update(
                    playerStatus="fighting"
                )
                
                return Fight.objects.create(
                    player_id=playerId,
                    creature_id=creatureId
                )

    @staticmethod
    def unlockFinishFight(fightId: int) -> None:
        Fight.objects.filter(
            id=fightId
        ).delete()

        cl = get_channel_layer()
        if cl is None:
            return
        async_to_sync(cl.group_send)(f"fight_{fightId}", {"type": "fight.finish.group", "fightId": fightId})

    @staticmethod
    def isFightStillActive(fightId: int) -> bool:
        fight = Fight.objects.filter(
            id=fightId
        ).exists()

        return fight

    @classmethod
    def attackMonster(cls, fightId: int) -> FightStatus | None:
        fight = Fight.objects.select_related(
            'creature',
            'player'
        ).filter(
            id=fightId
        ).first()

        if fight is None:
            return
        
        c: WorldCreature = fight.creature
        p: Player = fight.player
        fs = FightStatus()

        powerAttack = randint(1, p.playerPower)
        c.creatureLife = (c.creatureLife - powerAttack) if (c.creatureLife - powerAttack) > 0 else 0
        fs.creatureLife = c.creatureLife
        fs.playerLife = p.playerLife

        unlockFight = False

        if c.creatureLife <= 0:
            c.delete()
            unlockFight = True
            fs.isMonsterAlive = False
        else:
            c.save()

        if p.playerLife <= 0:
            p.playerStatus = "dead"
            p.save()
            unlockFight = True
            fs.isPlayerAlive = False

        if unlockFight:
            fs.isFightOver = True
            cls.unlockFinishFight(fightId)

        return fs

    @classmethod
    def attackPlayer(cls, fightId: int) -> FightStatus | None:
        fight = Fight.objects.select_related(
            'creature',
            'player'
        ).filter(
            id=fightId
        ).first()

        if fight is None:
            return
        
        c: WorldCreature = fight.creature
        p: Player = fight.player
        fs = FightStatus()

        powerAttack = randint(c.creatureLevel, c.creatureLevel+10)
        p.playerLife = (p.playerLife - powerAttack) if (p.playerLife - powerAttack) > 0 else 0
        fs.creatureLife = c.creatureLife
        fs.playerLife = p.playerLife

        #check item power logic etc.

        unlockFight = False

        if p.playerLife <= 0:
            p.playerStatus = "dead"
            p.save()
            unlockFight = True
            fs.isPlayerAlive = False
        else:
            p.save()

        if c.creatureLife <= 0:
            c.delete()
            unlockFight = True
            fs.isMonsterAlive = False

        if unlockFight:
            fs.isFightOver = True
            cls.unlockFinishFight(fightId)

        return fs
