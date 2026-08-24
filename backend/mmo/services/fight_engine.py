from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer

from django.db import transaction
from django.core.cache import cache

from mmo.models import Player, Fight, WorldCreature
from .constants import (
    LEVEL_MAX, PLAYER_IS_ATTACKING, TEMPO_MIN_ATTACK, TEMPO_MAX_ATTACK,
    MONSTER_MAX_ATTACK, MONSTER_MIN_ATTACK, PLAYER_POWER_ATTACK_VARIATION,
    MONSTER_POWER_ATTACK_VARIATION
)

from random import randint
from dataclasses import dataclass, asdict

@dataclass
class FightStatus:
    isPlayerAlive: bool = True
    isMonsterAlive: bool = True
    isFightOver: bool = False
    isPlayerAttacking: float = 0.0
    isCreatureAttacking: float = 0.0
    playerLife: int | None = None
    creatureLife: int | None = None
    creatureLevel: int = 1

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
    def setPlayerIsAttacking(playerId: int, playerLevel: int) -> float:
        attackTime = max(TEMPO_MIN_ATTACK, 
            TEMPO_MAX_ATTACK - ((TEMPO_MAX_ATTACK - TEMPO_MIN_ATTACK) * (playerLevel/LEVEL_MAX))
        )
        cache.set(PLAYER_IS_ATTACKING.format(playerId=playerId), True, timeout=attackTime)
        return attackTime

    @staticmethod
    def monsterAttackInterval(creatureLevel: int) -> float:
        attackTime = max(MONSTER_MIN_ATTACK, 
            MONSTER_MAX_ATTACK - ((MONSTER_MAX_ATTACK - MONSTER_MIN_ATTACK) * (creatureLevel/LEVEL_MAX))
        )
        return attackTime

    @staticmethod
    def canIAttack(playerId: int) -> bool:
        if cache.get(PLAYER_IS_ATTACKING.format(playerId=playerId)) is None:
            return True

        return False

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
    def unlockFinishFight(fightId: int, fs: FightStatus | None = None) -> None:
        f = Fight.objects.filter(
            id=fightId
        ).select_related(
            'player'
        )
        if not f:
            return
        
        p = f.first()
        if not p: #pyright
            return 

        with transaction.atomic():
            if p.player.playerStatus != "dead":
                p.player.playerStatus = "idle"
                p.player.save()

            f.delete()

        cl = get_channel_layer()
        if cl is None:
            return
        async_to_sync(cl.group_send)(
            f"fight_{fightId}", 
            {"type": "fight.finish.group", 
            "fightId": fightId,
            "fightStatus": asdict(fs) if fs else None}
        )

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
        playerAttackTime = 0.0

        if not cls.canIAttack(p.id):
            return
        else:
            playerAttackTime = cls.setPlayerIsAttacking(p.id, p.playerLevel)
        
        fs = FightStatus()
        fs.isPlayerAttacking = playerAttackTime

        # ADD ITEM POWER CALCULATION
        powerAttack = randint(
            int(p.playerPower*PLAYER_POWER_ATTACK_VARIATION), 
            p.playerPower #add items power later
        )
        c.creatureLife = (c.creatureLife - powerAttack) if (c.creatureLife - powerAttack) > 0 else 0
        fs.creatureLife = c.creatureLife
        fs.playerLife = p.playerLife

        unlockFight = False

        with transaction.atomic():
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
            cls.unlockFinishFight(fightId, fs)

        return fs

    @classmethod
    def attackPlayer(cls, fightId: int, isCreatureAttacking: float = 0.0) -> FightStatus | None:
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
        fs.isCreatureAttacking = cls.monsterAttackInterval(c.creatureLevel)

        powerAttack = randint(
            int((c.creatureLevel+10)*MONSTER_POWER_ATTACK_VARIATION),
            c.creatureLevel+10
        )
        p.playerLife = (p.playerLife - powerAttack) if (p.playerLife - powerAttack) > 0 else 0
        fs.creatureLife = c.creatureLife
        fs.creatureLevel = c.creatureLevel
        fs.playerLife = p.playerLife

        #check item power logic etc.

        unlockFight = False

        with transaction.atomic():
            if p.playerLife <= 0:
                p.playerStatus = "dead"
                unlockFight = True
                fs.isPlayerAlive = False

            if c.creatureLife <= 0:
                c.delete()
                unlockFight = True
                fs.isMonsterAlive = False

            p.save()

        if unlockFight:
            fs.isFightOver = True
            cls.unlockFinishFight(fightId, fs)

        return fs

    @classmethod
    def playerFlee(cls, fightId: int):
        if not cls.isFightStillActive(fightId):
            return None
        
        f = Fight.objects.select_related('player').filter(id=fightId).first()
        if f is None:
            return None
        p: Player = f.player

        fs = FightStatus(
            isPlayerAlive=True if p.playerStatus != "dead" else False,
            isFightOver=True,
            playerLife=p.playerLife
        )

        cls.unlockFinishFight(fightId, fs)

            