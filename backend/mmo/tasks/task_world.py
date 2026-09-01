from celery import shared_task

from django.db.models import F
from django.utils import timezone

from mmo.models import World, WorldCreature, Player, Item
from mmo.data.monster_names import MONSTER_NAMES
from mmo.services.player_engine import PlayerEngine
from mmo.services.constants import MONSTER_LIFE_VARIATION, MONSTER_BASE_LIFE

from datetime import timedelta
import random

@shared_task
def respawn_creatures() -> None:
    w = World.objects.all()
    for i in w:
        cw = WorldCreature.objects.filter(
            world=i.id
        )
        if cw.count() < i.world_total_creatures:
            diff = i.world_total_creatures - cw.count()
            for _ in range(diff):
                creature_name = random.choice(MONSTER_NAMES)
                creature_level = random.randint(i.world_min_level, i.world_max_level)
                chance_drop = int((creature_level * 100) / i.world_max_level)
                creature_life = int(MONSTER_BASE_LIFE + (creature_level * MONSTER_LIFE_VARIATION))
                WorldCreature.objects.create(
                    world=i,
                    creature_name=creature_name,
                    creature_level=creature_level,
                    creature_chance_drop=chance_drop,
                    creature_life=creature_life
                )

@shared_task
def recover_player_status() -> None:
    """
        I know that this can be better with a better control of it.
        But for a small project it fits well, I will maintain this for now.
    """
    players = Player.objects.select_related(
        "player_equipped_weapon__item",
        "player_equipped_armour__item"
    ).exclude(
        player_status__in=[Player.PlayerStatus.DEAD],
    ).exclude(
        player_life=F('player_max_life'),
        player_stamina=F('player_max_stamina')
    ).all()

    if len(players) > 0:
        PlayerEngine.recover_players_status(players)

@shared_task
def tick() -> None:
    respawn_creatures.delay()
    recover_player_status.delay()

@shared_task
def clean_orphan_items() -> None:
    time_since = timezone.now() - timedelta(days=1)

    orphan_items = Item.objects.filter(
        item_created_date__lte=time_since,
        playerinventory__isnull=True
    ).all()

    if len(orphan_items) > 0:
        orphan_items.delete()
