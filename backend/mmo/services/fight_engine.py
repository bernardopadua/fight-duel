from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer

from django.db import transaction
from django.core.cache import cache
from django.forms import model_to_dict

from mmo.models import Player, Fight, WorldCreature
from mmo.services.player_engine import PlayerEngine
from .constants import (
    LEVEL_MAX, PLAYER_IS_ATTACKING, TEMPO_MIN_ATTACK, TEMPO_MAX_ATTACK,
    MONSTER_MAX_ATTACK, MONSTER_MIN_ATTACK, PLAYER_POWER_ATTACK_VARIATION,
    MONSTER_POWER_ATTACK_VARIATION
)

from mmo.services.drop_engine import DropEngine

from random import randint
from dataclasses import dataclass, asdict

from typing import Any

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
    creatureChanceDrop: int = 0

@dataclass
class FightStart:
    fightId: int
    creatureName: str
    creatureLevel: int

class FightEngine:

    @classmethod
    def shouldIFight(cls, playerId: int) -> FightStart | None:
        p = Player.objects.filter(id=playerId).first()
        if not p:
            return None

        creature = WorldCreature.objects.filter(
            fight__isnull=True
        ).filter(
            creature_level__lte=p.player_level+4 #TODO: make better the random fight levels, not just +4
        ).order_by('?').first()
        if not creature:
            creature = WorldCreature.objects.filter(
                fight__isnull=True
            ).order_by('?').first()

        if not creature:
            return None

        if not Player.objects.filter(
            fight__isnull=True,
            id=playerId
        ).exists():
            return None

        fight = cls.lockFight(creature.id, playerId)
        if fight is None:
            return None
        
        return FightStart(
            fightId=fight.id,
            creatureName=creature.creature_name,
            creatureLevel=creature.creature_level
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
                    player_status="fighting"
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
            "player",
            "creature"
        ).first()
        if not f:
            return
        
        p = f.player
        if not p: #pyright
            return 

        with transaction.atomic():
            if p.player_status != "dead":
                p.player_status = "idle"
                p.save()
            
            if fs and not fs.isMonsterAlive:
                f.creature.delete() #this will delete fight
            else:
                f.delete()

            if not fs:
                #TODO: Logging here
                return 

            itemsDict: list[dict[str, Any]] = []
            if fs.isPlayerAlive and not fs.isMonsterAlive:
                items = DropEngine.dropItems(fs.creatureLevel, fs.creatureChanceDrop)
                itemsDict = [i.to_dict() for i in items]

                #thinking on how I'm going to treat this
                #but for now I think I will just let the client ask for a rest endpoint for player status refreshing
                PlayerEngine.levelUp(p, fs.creatureLevel)

        cl = get_channel_layer()
        if cl is None:
            return

        async_to_sync(cl.group_send)(
            f"fight_{fightId}", 
            {
                "type": "fight.finish.group", 
                "fightId": fightId,
                "fightStatus": asdict(fs) if fs else None,
                "itemsDrop": itemsDict
            }
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
            playerAttackTime = cls.setPlayerIsAttacking(p.id, p.player_level)
        
        fs = FightStatus()
        fs.isPlayerAttacking = playerAttackTime

        totalPower = PlayerEngine.getPlayerTotalPower(p)
        powerAttack = randint(
            int(totalPower*PLAYER_POWER_ATTACK_VARIATION), 
            totalPower
        )
        powerAttack = 100 #I'm testing, keeping it for now.
        c.creature_life = (c.creature_life - powerAttack) if (c.creature_life - powerAttack) > 0 else 0
        fs.creatureLife = c.creature_life
        fs.playerLife = p.player_life

        unlockFight = False

        with transaction.atomic():
            if c.creature_life <= 0:
                fs.creatureChanceDrop = c.creature_chance_drop
                fs.creatureLevel = c.creature_level
                #c.delete()
                unlockFight = True
                fs.isMonsterAlive = False
            else:
                c.save()

            if p.player_life <= 0:
                p.player_status = "dead"
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
            'player__player_equipped_armour__item',
        ).filter(
            id=fightId
        ).first()

        if fight is None:
            return
        
        c: WorldCreature = fight.creature
        p: Player = fight.player
        fs = FightStatus()
        fs.isCreatureAttacking = cls.monsterAttackInterval(c.creature_level)

        powerAttack = randint(
            int((c.creature_level+10)*MONSTER_POWER_ATTACK_VARIATION),
            c.creature_level+10
        )
        defensePower = p.player_equipped_armour.item.item_power if p.player_equipped_armour else 0
        totalDamage = max(0, (powerAttack-defensePower))
        p.player_life = (p.player_life - totalDamage) if (p.player_life - totalDamage) > 0 else 0
        fs.creatureLife = c.creature_life
        fs.creatureLevel = c.creature_level
        fs.playerLife = p.player_life

        #check item power logic etc.

        unlockFight = False

        with transaction.atomic():
            if p.player_life <= 0:
                p.player_status = "dead"
                unlockFight = True
                fs.isPlayerAlive = False

            if c.creature_life <= 0:
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
            isPlayerAlive=True if p.player_status != "dead" else False,
            isFightOver=True,
            playerLife=p.player_life
        )

        cls.unlockFinishFight(fightId, fs)

