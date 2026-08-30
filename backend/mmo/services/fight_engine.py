from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer

from django.db import transaction
from django.core.cache import cache
from django.db.models import Q

from mmo.models import Player, Fight, WorldCreature
from mmo.services.player_engine import PlayerEngine
from .constants import (
    LEVEL_MAX, PLAYER_IS_ATTACKING, TEMPO_MIN_ATTACK, TEMPO_MAX_ATTACK,
    MONSTER_MAX_ATTACK, MONSTER_MIN_ATTACK, PLAYER_POWER_ATTACK_VARIATION,
    MONSTER_POWER_ATTACK_VARIATION, UNLOCK_FIGHT_LOCK
)

from mmo.services.drop_engine import DropEngine

from random import randint
from dataclasses import dataclass

from typing import Any

@dataclass
class FightStatus:
    is_player_alive: bool = True
    is_monster_alive: bool = True
    is_fight_over: bool = False
    is_player_attacking: float = 0.0
    is_creature_attacking: float = 0.0
    player_life: int | None = None
    creature_life: int | None = None
    creature_level: int = 1
    creature_chance_drop: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "isPlayerAlive": self.is_player_alive,
            "isMonsterAlive": self.is_monster_alive,
            "isFightOver": self.is_fight_over,
            "isPlayerAttacking": self.is_player_attacking,
            "isCreatureAttacking": self.is_creature_attacking,
            "playerLife": self.player_life,
            "creatureLife": self.creature_life,
            "creatureLevel": self.creature_level,
            "creatureChanceDrop": self.creature_chance_drop
        }

@dataclass
class FightStart:
    fight_id: int
    creature_name: str
    creature_level: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "fightId": self.fight_id,
            "creatureName": self.creature_name,
            "creatureLevel": self.creature_level
        }

class FightEngine:

    @classmethod
    def should_fight(cls, player_id: int) -> FightStart | None:
        p = Player.objects.filter(
            id=player_id
        ).exclude(
            player_status__in=[Player.PlayerStatus.DEAD, Player.PlayerStatus.FIGHTING]
        ).exclude(
            player_world__isnull=True
        ).first()
        if not p:
            return None

        creature = WorldCreature.objects.filter(
            fight__isnull=True
        ).filter(
            world=p.player_world,
            creature_level__lte=p.player_level+4 #TODO: make better the random fight levels, not just +4
        ).order_by('?').first()
        if not creature:
            creature = WorldCreature.objects.filter(
                fight__isnull=True,
                world=p.player_world
            ).order_by('?').first()

        if not creature:
            return None

        if FightEngine.is_player_in_a_fight(player_id):
            return None

        fight = cls.lock_fight(creature.id, player_id)
        if fight is None:
            return None
        
        return FightStart(
            fight_id=fight.id,
            creature_name=creature.creature_name,
            creature_level=creature.creature_level
        )

    @staticmethod
    def set_player_attacking(player: Player) -> float:
        if player.player_life <= 0 or player.player_status != Player.PlayerStatus.FIGHTING:
            return 0.0

        attack_time = max(TEMPO_MIN_ATTACK, 
            TEMPO_MAX_ATTACK - ((TEMPO_MAX_ATTACK - TEMPO_MIN_ATTACK) * (player.player_level/LEVEL_MAX))
        )
        if cache.add(PLAYER_IS_ATTACKING.format(player_id=player.id), True, timeout=attack_time):
            return attack_time
        
        return 0.0

    @staticmethod
    def monster_attack_interval(creature_level: int) -> float:
        attack_time = max(MONSTER_MIN_ATTACK, 
            MONSTER_MAX_ATTACK - ((MONSTER_MAX_ATTACK - MONSTER_MIN_ATTACK) * (creature_level/LEVEL_MAX))
        )
        return attack_time

    @staticmethod
    def lock_fight(creature_id: int, player_id: int) -> Fight | None:
        #maybe some more checking here?
        
        with transaction.atomic():
            is_creature_locked = WorldCreature.objects.select_for_update(
                skip_locked=True
            ).filter(id=creature_id).first()

            if is_creature_locked is None:
                #TODO: Treat with a exception here
                return

            Player.objects.filter(
                id=player_id
            ).update(
                player_status=Player.PlayerStatus.FIGHTING
            )
            
            return Fight.objects.create(
                player_id=player_id,
                creature_id=creature_id
            )

    @staticmethod
    def unlock_finish_fight(fight_id: int, fs: FightStatus | None = None) -> None:
        f = Fight.objects.filter(
            id=fight_id
        ).select_related(
            "player",
            "creature"
        ).first()
        if not f:
            return
        
        p: Player = f.player
        if not p: #pyright
            return 

        with transaction.atomic():
            if p.player_status != Player.PlayerStatus.DEAD:
                p.player_status = Player.PlayerStatus.IDLE
            
            if fs and not fs.is_monster_alive:
                f.creature.delete() #this will delete fight
            else:
                f.delete()

            if not fs:
                #TODO: Logging here
                return 

            items_dict: list[dict[str, Any]] = []
            if fs.is_player_alive and not fs.is_monster_alive:
                items, currency = DropEngine.drop_items(fs.creature_level, fs.creature_chance_drop)
                items_dict = [i.to_dict() for i in items]

                p.player_currency += currency

                #thinking on how I'm going to treat this
                #but for now I think I will just let the client ask for a rest endpoint for player status refreshing
                PlayerEngine.level_up(p, fs.creature_level)

            p.save(update_fields=["player_status", "player_currency"])

        cl = get_channel_layer()
        if cl is None:
            return

        async_to_sync(cl.group_send)(
            f"fight_{fight_id}", 
            {
                "type": "fight.finish.group", 
                "fightId": fight_id,
                "fightStatus": fs.to_dict() if fs else None,
                "itemsDrop": items_dict
            }
        )

    @staticmethod
    def is_fight_still_active(fight_id: int) -> bool:
        fight = Fight.objects.filter(
            id=fight_id
        ).exists()

        return fight

    @staticmethod
    def is_player_in_a_fight(player_id: int) -> bool:
        return Fight.objects.filter(
            Q(player_id=player_id) | Q(opponent_id=player_id)
        ).exists()

    @classmethod
    def attack_monster(cls, fight_id: int) -> FightStatus | None:
        with transaction.atomic():
            fight = Fight.objects.select_for_update(of=['self']).select_related(
                'creature',
                'player',
                'player__player_equipped_weapon__item',
                'player__player_equipped_armour__item'
            ).filter(
                id=fight_id
            ).first()

            if fight is None:
                return

            c: WorldCreature = fight.creature
            p: Player = fight.player

            if not (player_attack_time := cls.set_player_attacking(p)):
                return

            fs = FightStatus()
            fs.is_player_attacking = player_attack_time

            total_power = PlayerEngine.get_player_total_power(p)
            power_attack = randint(
                int(total_power * PLAYER_POWER_ATTACK_VARIATION), 
                total_power
            )
            c.creature_life = (c.creature_life - power_attack) if (c.creature_life - power_attack) > 0 else 0
            fs.creature_life = c.creature_life
            fs.player_life = p.player_life

            unlock_fight = False

            if c.creature_life <= 0:
                fs.creature_chance_drop = c.creature_chance_drop
                fs.creature_level = c.creature_level
                unlock_fight = True
                fs.is_monster_alive = False
            else:
                c.save(update_fields=["creature_life"])

        if unlock_fight and \
            cache.add(UNLOCK_FIGHT_LOCK.format(fight_id=fight_id), True, timeout=2) \
        :
            fs.is_fight_over = True
            cls.unlock_finish_fight(fight_id, fs)

        return fs

    @classmethod
    def attack_player(cls, fight_id: int, is_creature_attacking: float = 0.0) -> FightStatus | None:
        with transaction.atomic():
            fight = Fight.objects.select_for_update(
                of=('self', 'player')
            ).select_related(
                'creature',
                'player__player_equipped_armour__item',
            ).filter(
                id=fight_id
            ).first()

            if fight is None:
                return
            
            c: WorldCreature = fight.creature
            p: Player = fight.player
            fs = FightStatus()
            fs.is_creature_attacking = cls.monster_attack_interval(c.creature_level)

            power_attack = randint(
                int((c.creature_level + 10) * MONSTER_POWER_ATTACK_VARIATION),
                c.creature_level + 10
            )
            defense_power = p.player_equipped_armour.item.item_power if p.player_equipped_armour else 0
            total_damage = max(0, (power_attack - defense_power))
            p.player_life = (p.player_life - total_damage) if (p.player_life - total_damage) > 0 else 0
            fs.creature_life = c.creature_life
            fs.creature_level = c.creature_level
            fs.player_life = p.player_life

            unlock_fight = False

            with transaction.atomic():
                if p.player_life <= 0:
                    p.player_status = Player.PlayerStatus.DEAD
                    unlock_fight = True
                    fs.is_player_alive = False
                    PlayerEngine.player_dead_penalty(p)

                p.save(update_fields=["player_status", "player_life"])

        if unlock_fight and \
            cache.add(UNLOCK_FIGHT_LOCK.format(fight_id=fight_id), True, timeout=2) \
        :
            fs.is_fight_over = True
            cls.unlock_finish_fight(fight_id, fs)

        return fs

    @classmethod
    def player_flee(cls, fight_id: int) -> None:
        if not cls.is_fight_still_active(fight_id):
            return None
        
        f = Fight.objects.select_related('player').filter(id=fight_id).first()
        if f is None:
            return None
        p: Player = f.player

        fs = FightStatus(
            is_player_alive=True if p.player_status != Player.PlayerStatus.DEAD else False,
            is_fight_over=True,
            player_life=p.player_life
        )

        cls.unlock_finish_fight(fight_id, fs)

