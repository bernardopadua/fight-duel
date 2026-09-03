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
from mmo.constants import FIGHT_GROUP, USER_CHANNEL_WS_LOGGED
from mmo.services.drop_engine import DropEngine

from mmo.tasks.task_player import apply_death_penalty_to_player

from random import randint
from dataclasses import dataclass

from typing import Any, TypeAlias
import random, logging

logger = logging.getLogger("fight_engine")

@dataclass
class FightPvPStatus:
    player_id: int = 0
    opponent_id: int = 0

    is_player_alive: bool = True
    is_opponent_alive: bool = True
    is_fight_over: bool = False
    player_life: int | None = None
    player_stamina: int | None = None
    opponent_life: int | None = None
    opponent_stamina: int | None = None
    player_level: int = 1
    opponent_level: int = 1
    player_name: str = ''
    opponent_name: str = ''

    def to_dict(self) -> dict[str, Any]:
        return_dict = {
            "isPlayerAlive": self.is_player_alive,
            "isOpponentAlive": self.is_opponent_alive,
            "isFightOver": self.is_fight_over,
            "playerLife": self.player_life,
            "opponentLife": self.opponent_life,
            "playerStamina": self.player_stamina,
            "opponentStamina": self.opponent_stamina,
            "playerLevel": self.player_level,
            "opponentLevel": self.opponent_level,
            "playerName": self.player_name,
            "opponentName": self.opponent_name
        }
        return return_dict
FightPvPStatusPlayer: TypeAlias = FightPvPStatus
FightPvPStatusOpponent: TypeAlias = FightPvPStatus

@dataclass
class FightStatus:
    is_player_alive: bool = True
    is_monster_alive: bool = True
    is_fight_over: bool = False
    is_player_attacking: float = 0.0
    is_creature_attacking: float = 0.0
    player_life: int | None = None
    player_stamina: int | None = None
    creature_life: int | None = None
    creature_level: int = 1
    creature_chance_drop: int = 0

    def to_dict(self) -> dict[str, Any]:
        return_dict = {
            "isPlayerAlive": self.is_player_alive,
            "isMonsterAlive": self.is_monster_alive,
            "isFightOver": self.is_fight_over,
            "isPlayerAttacking": self.is_player_attacking,
            "isCreatureAttacking": self.is_creature_attacking,
            "playerLife": self.player_life,
            "playerStamina": self.player_stamina,
            "creatureLife": self.creature_life,
            "creatureLevel": self.creature_level,
            "creatureChanceDrop": self.creature_chance_drop
        }
        return return_dict

@dataclass
class FightStart:
    fight_id: int
    player: Player
    opponent: Player | None
    creature_name: str | None
    creature_level: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "fightId": self.fight_id,
            "creatureName": self.creature_name,
            "creatureLevel": self.creature_level
        }

class FightEngine:

    @staticmethod
    def calculate_chance_matchmaking(player: Player) -> int:
        return random.randint(1, 100)

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

        if FightEngine.is_player_in_a_fight(player_id):
            return None

        # Should I fight with a player?
        opponent: Player | None = None
        creature: WorldCreature | None = None
        if cls.calculate_chance_matchmaking(p) <= 10:
            opponent = Player.objects.filter(
                player_world=p.player_world
            ).exclude(
                id=player_id
            ).exclude(
                player_status__in=[Player.PlayerStatus.DEAD, Player.PlayerStatus.FIGHTING]
            ).exclude(
                player_world__isnull=True
            ).order_by('?').first()

            if opponent and cache.get(USER_CHANNEL_WS_LOGGED.format(user_id=opponent.user_id)) is None:
                opponent = None

        if not opponent:
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

        fight = cls.lock_fight(
            player_id,
            opponent_id=opponent.id if opponent else None,
            creature_id=creature.id if creature else None
        )
        if not fight:
            return None

        return FightStart(
            fight_id=fight.id,
            player=p,
            opponent=opponent,
            creature_name=creature.creature_name if creature else None,
            creature_level=creature.creature_level if creature else None
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
    def lock_fight(player_id: int, opponent_id: int | None = None, creature_id: int | None = None) -> Fight | None:
        #maybe some more checking here?
        
        with transaction.atomic():
            is_opponent_locked: Player | None = None
            is_creature_locked: WorldCreature | None = None
            players_id: list = []

            if opponent_id:
                # Locking creator and opponent for fight creation
                players_id = sorted([player_id, opponent_id])
                players = Player.objects.select_for_update(
                    skip_locked=True
                ).exclude(
                    player_status__in=[Player.PlayerStatus.DEAD, Player.PlayerStatus.FIGHTING]
                ).filter(id__in=players_id).all()
                
                if len(players) != 2:
                    return None

                if Fight.objects.filter(
                    Q(player_id__in=players_id) |
                    Q(opponent_id__in=players_id)
                ).exists():
                    return None

                is_opponent_locked = next((p for p in players if p.id == opponent_id))
            else:
                # Locking player to avoid double MOVE
                is_player_locked = Player.objects.select_for_update(
                    skip_locked=True
                ).exclude(
                    player_status__in=[Player.PlayerStatus.DEAD, Player.PlayerStatus.FIGHTING]
                ).filter(id=player_id).first()
                
                if is_player_locked is None:
                    logger.error("Player %s is not locked", player_id)
                    return None

                # Locking creature for fight creation
                is_creature_locked = WorldCreature.objects.select_for_update(
                    skip_locked=True
                ).filter(id=creature_id).first()

                if is_creature_locked is None:
                    logger.error("Creature %s is not locked", creature_id)
                    return None
                
                if Fight.objects.filter(
                    Q(player_id=player_id) |
                    Q(opponent_id=player_id) |
                    Q(creature_id=creature_id)
                ).exists():
                    return None

            if is_opponent_locked:
                Player.objects.filter(
                    id__in=players_id
                ).update(
                    player_status=Player.PlayerStatus.FIGHTING
                )
            elif is_creature_locked:
                Player.objects.filter(
                    id=player_id
                ).update(
                    player_status=Player.PlayerStatus.FIGHTING
                )
            else:
                logger.error("No opponent or creature found for player %s", player_id)
                return None
            
            return Fight.objects.create(
                player_id=player_id,
                creature_id=creature_id if creature_id else None,
                opponent=is_opponent_locked if is_opponent_locked else None
            )

    @staticmethod
    def unlock_finish_fight_pve(fight_id: int, fs: FightStatus | None = None) -> None:
        f = Fight.objects.filter(
            id=fight_id
        ).select_related(
            'player',
            'creature'
        ).first()
        if not f:
            logger.warning("Fight %s not found", fight_id)
            return
        
        p: Player = f.player
        if not p: #pyright
            return 

        with transaction.atomic():
            if p.player_status != Player.PlayerStatus.DEAD:
                p.player_status = Player.PlayerStatus.IDLE

            if f.creature and fs and not fs.is_monster_alive:
                f.creature.delete() #this will delete fight
            else:
                f.delete()

            items_dict: list[dict[str, Any]] = []
            if fs and fs.is_player_alive and not fs.is_monster_alive:
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
            FIGHT_GROUP.format(fight_id=fight_id), 
            {
                "type": "fight.finish.group", 
                "fightId": fight_id,
                "fightStatus": fs.to_dict() if fs else None,
                "itemsDrop": items_dict
            }
        )

    @staticmethod
    def unlock_finish_fight_pvp(
        fight_id: int, 
        player_id: int, 
        fs: FightPvPStatus | None = None,
        fs_o: FightPvPStatus | None = None
    ) -> None:
        """
            Unlocks the fight and updates the player status.
            Unlocks the fight after the fight finishes, when the player flees, when the player rejects.
            It also runs on timeout fights where neither player accepted nor rejected.
            When fs and fs_o are None, it means the fight timed out, aborted or rejected.
            When fight times out, player_id is the original player who created the fight.
            Args:
                fight_id (int): Fight id
                player_id (int): Player id (the caller, attacker, owner of the action)
                fs (FightPvPStatus | None, optional): Fight status. Defaults to None.
                fs_o (FightPvPStatus | None, optional): Fight status. Defaults to None.
        """
        
        f = Fight.objects.filter(
            id=fight_id
        ).select_related(
            'player',
            'opponent'
        ).first()
        if not f:
            logger.warning("Fight %s not found", fight_id)
            return
        
        p: Player = f.player if f.player.id == player_id else f.opponent
        o: Player = f.opponent if p == f.player else f.player
        if not p or not o: #pyright
            return 

        with transaction.atomic():
            if p.player_status != Player.PlayerStatus.DEAD:
                p.player_status = Player.PlayerStatus.IDLE

            if o.player_status != Player.PlayerStatus.DEAD:
                o.player_status = Player.PlayerStatus.IDLE
            
            f.delete()

            items_dict: list[dict[str, Any]] = []
            if fs and fs.is_fight_over and fs.is_player_alive and not fs.is_opponent_alive:
                items, currency = DropEngine.drop_items(o.player_level, DropEngine.calculate_chance_drop_by_player(o))
                items_dict = [i.to_dict() for i in items]

                p.player_currency += currency

                #thinking on how I'm going to treat this
                #but for now I think I will just let the client ask for a rest endpoint for player status refreshing
                PlayerEngine.level_up(p, o.player_level)

            p.save(update_fields=["player_status", "player_currency"])
            o.save(update_fields=["player_status"])

        cl = get_channel_layer()
        if cl is None:
            return

        p_channel = cache.get(USER_CHANNEL_WS_LOGGED.format(user_id=p.user_id))
        o_channel = cache.get(USER_CHANNEL_WS_LOGGED.format(user_id=o.user_id))
        if not p_channel or not o_channel:
            logger.error('Fight %s p_channel or o_channel not found', fight_id)

        if p_channel and fs:
            async_to_sync(cl.send)(
                p_channel,
                {
                    "type": "fight.finish.group", 
                    "fightId": fight_id,
                    "fightStatus": fs.to_dict(),
                    "itemsDrop": items_dict
                }
            )
        if o_channel and fs_o:
            async_to_sync(cl.send)(
                o_channel,
                {
                    "type": "fight.finish.group", 
                    "fightId": fight_id,
                    "fightStatus": fs_o.to_dict()
                }
            )
        
        #fight rejected None for fight status
        if not fs and not fs_o:
            async_to_sync(cl.group_send)(
                FIGHT_GROUP.format(fight_id=fight_id),
                {
                    "type": "fight.finish.group", 
                    "fightId": fight_id
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
    def player_flee(
        cls, 
        fight_id: int, 
        player_id: int, *, 
        is_pvp: bool = False
    ) -> None:
        if not cls.is_fight_still_active(fight_id):
            return None
        
        f = Fight.objects.select_related(
            'player',
            'opponent'
        ).filter(
            id=fight_id
        ).first()
        if f is None:
            return None

        p: Player = f.player if f.player.id == player_id else f.opponent
        o: Player = f.opponent if p == f.player else f.player

        if is_pvp:
            fs = FightPvPStatus(
                is_player_alive=True if p.player_status != Player.PlayerStatus.DEAD else False,
                is_opponent_alive=True if o.player_status != Player.PlayerStatus.DEAD else False,
                player_life=p.player_life,
                opponent_life=o.player_life,
                player_level=p.player_level,
                opponent_level=o.player_level,
                is_fight_over=True,
                player_name=p.player_name,
                opponent_name=o.player_name
            )
            fs_o = FightPvPStatus(
                is_player_alive=True if o.player_status != Player.PlayerStatus.DEAD else False,
                is_opponent_alive=True if p.player_status != Player.PlayerStatus.DEAD else False,
                player_life=o.player_life,
                opponent_life=p.player_life,
                player_level=o.player_level,
                opponent_level=p.player_level,
                is_fight_over=True,
                player_name=o.player_name,
                opponent_name=p.player_name
            )
            
            if cache.add(UNLOCK_FIGHT_LOCK.format(fight_id=fight_id), True, timeout=2):
                cls.unlock_finish_fight_pvp(fight_id, player_id, fs, fs_o)
            
            return

        fs = FightStatus(
            is_player_alive=True if p.player_status != Player.PlayerStatus.DEAD else False,
            is_fight_over=True,
            player_life=p.player_life
        )

        if cache.add(UNLOCK_FIGHT_LOCK.format(fight_id=fight_id), True, timeout=2):
            cls.unlock_finish_fight_pve(fight_id, fs)

    @classmethod
    def attack_monster(cls, fight_id: int) -> FightStatus | None:
        with transaction.atomic():
            attack_applied = False
            fight = Fight.objects.select_for_update(of=['self']).select_related(
                'creature',
                'player',
                'player__player_equipped_weapon__item',
                'player__player_equipped_armour__item'
            ).filter(
                id=fight_id,
                player__player_stamina__gt=0
            ).first()

            if fight is None:
                return

            c: WorldCreature = fight.creature
            p: Player = fight.player

            fs = FightStatus()
            fs.creature_chance_drop = c.creature_chance_drop
            fs.creature_level = c.creature_level
            fs.player_life = p.player_life
            fs.player_stamina = p.player_stamina

            total_power = PlayerEngine.get_player_total_power(p)
            power_attack = randint(
                int(total_power * PLAYER_POWER_ATTACK_VARIATION), 
                total_power
            )
            stamina_usage = PlayerEngine.get_player_stamina_usage_fight(
                p, 
                total_power=total_power
            )

            if p.player_stamina >= stamina_usage:
                attack_applied = True

                c.creature_life = max(0, c.creature_life - power_attack)
                p.player_stamina = max(0, p.player_stamina - stamina_usage)

                fs.player_stamina = p.player_stamina
                fs.creature_life = c.creature_life

            unlock_fight = False
            if attack_applied:
                if not (player_attack_time := cls.set_player_attacking(p)):
                    return
                fs.is_player_attacking = player_attack_time
                
                if c.creature_life <= 0:
                    unlock_fight = True
                    fs.is_monster_alive = False
                else:
                    c.save(update_fields=["creature_life"])

                p.save(update_fields=["player_stamina"])
            else:
                return None
        if unlock_fight and \
            cache.add(UNLOCK_FIGHT_LOCK.format(fight_id=fight_id), True, timeout=2) \
        :
            fs.is_fight_over = True
            cls.unlock_finish_fight_pve(fight_id, fs)

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
            defense_power = PlayerEngine.get_player_defense_power(p)
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
            cls.unlock_finish_fight_pve(fight_id, fs)

        return fs

    @classmethod
    def attack_pvp_player(cls, fight_id: int, player_id: int) -> tuple[FightPvPStatusPlayer | None, FightPvPStatusOpponent | None]:
        with transaction.atomic():
            attack_applied = False
            fight = Fight.objects.select_for_update(of=['self']).select_related(
                'player',
                'opponent',
                'player__player_equipped_armour__item',
                'player__player_equipped_weapon__item',
                'opponent__player_equipped_armour__item',
                'opponent__player_equipped_weapon__item'
            ).filter(
                id=fight_id
            ).first()
            if not fight:
                return None, None
            
            p: Player = fight.player if fight.player.id == player_id else fight.opponent
            o: Player = fight.opponent if p == fight.player else fight.player
            
            fs = FightPvPStatus()
            fs.player_id = p.id
            fs.opponent_id = o.id
            fs.is_player_alive = p.player_status != Player.PlayerStatus.DEAD
            fs.is_opponent_alive = o.player_status != Player.PlayerStatus.DEAD
            fs.is_fight_over = False
            fs.player_life = p.player_life
            fs.opponent_life = o.player_life
            fs.player_stamina = p.player_stamina
            fs.opponent_stamina = o.player_stamina
            fs.opponent_level = o.player_level
            fs.player_name = p.player_name
            fs.opponent_name = o.player_name

            fs_o: FightPvPStatus = FightPvPStatus(
                player_id=o.id,
                opponent_id=p.id,
                is_player_alive=o.player_status != Player.PlayerStatus.DEAD,
                is_opponent_alive=p.player_status != Player.PlayerStatus.DEAD,
                is_fight_over=False,
                player_life=o.player_life,
                opponent_life=p.player_life,
                player_stamina=o.player_stamina,
                opponent_stamina=p.player_stamina,
                player_level=o.player_level,
                opponent_level=p.player_level,
                player_name=o.player_name,
                opponent_name=p.player_name
            )

            power_attack = PlayerEngine.get_player_total_power(p)
            defense_power = PlayerEngine.get_player_defense_power(o)
            stamina_usage = PlayerEngine.get_player_stamina_usage_fight(p, total_power=power_attack)
            total_damage = max(0, (power_attack - defense_power))
            
            if p.player_stamina >= stamina_usage:
                attack_applied = True
                o.player_life = max(0, (o.player_life - total_damage))
                p.player_stamina = max(0, (p.player_stamina - stamina_usage))

                fs.player_life = p.player_life
                fs.opponent_life = o.player_life
                fs.player_stamina = p.player_stamina
                fs.opponent_stamina = o.player_stamina
                fs.player_level = p.player_level

                fs_o.player_life = o.player_life
                fs_o.opponent_life = p.player_life
                fs_o.player_stamina = o.player_stamina
                fs_o.opponent_stamina = p.player_stamina

                if not cls.set_player_attacking(p):
                    return None, None

            unlock_fight = False

            if attack_applied:
                if o.player_life <= 0:
                    o.player_status = Player.PlayerStatus.DEAD
                    unlock_fight = True
                    fs.is_opponent_alive = False
                    
                    fs_o.is_player_alive = False
                    fs_o.is_opponent_alive = True

                    transaction.on_commit(
                        lambda: apply_death_penalty_to_player.delay(o.id)
                    )
                
                o.save(update_fields=["player_status", "player_life"])
                p.save(update_fields=["player_stamina"])
            else:
                return None, None

        if unlock_fight and cache.add(UNLOCK_FIGHT_LOCK.format(fight_id=fight_id), True, timeout=2):
            fs.is_fight_over = True
            fs_o.is_fight_over = True
            cls.unlock_finish_fight_pvp(fight_id, player_id, fs=fs, fs_o=fs_o)
            return None, None

        return fs, fs_o
