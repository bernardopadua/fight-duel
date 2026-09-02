from unittest.mock import patch

from celery.contrib.testing.worker import start_worker

from django.contrib.auth.models import User
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from django.core.cache import cache

from core.settings import CELERY_REDIS_HOST_DB
from core.celery import app

from mmo.models import Item, Player, World, WorldCreature, Fight, PlayerInventory
from mmo.services.fight_engine import FightEngine
from mmo.tasks.task_world import (
    clean_orphan_items, respawn_creatures, recover_player_status,
    revive_dead_players
)
from mmo.tasks.task_fight import monster_attack
from mmo.tasks.task_matchmaking import clean_up_matchmaking_fight
from mmo.tasks.task_player import apply_death_penalty_to_player
from mmo.constants import USER_CHANNEL_WS_LOGGED, MATCHMAKING_IN_FIGHT

from datetime import timedelta

@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "mmo-tasks-tests"
        }
    }
)
class MMOCeleryWorkerTests(TransactionTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.worker = start_worker(app, perform_ping_check=False)
        cls.worker.__enter__()

        app.conf.update(
            result_backend=CELERY_REDIS_HOST_DB.format(db='15'),
            broker_url=CELERY_REDIS_HOST_DB.format(db='15')
        )

    @classmethod
    def tearDownClass(cls):
        cls.worker.__exit__(None, None, None)
        super().tearDownClass()
    
    def setUp(self) -> None:
        cache.clear()

        self.user = User.objects.create_user(username='test', email='test@test.com', password='123456')

        self.world = World.objects.create(
            world_name='TestWorld',
            world_total_creatures=2,
            world_min_level=1,
            world_max_level=10
        )

        self.player_power = 999
        self.player_life = 100
        self.player = Player.objects.create(
            player_name='TestPlayer',
            player_level=10,
            player_power=self.player_power,
            player_life=self.player_life,
            user=self.user,
            player_world=self.world
        )

        self.user_2 = User.objects.create_user(username='test2', email='test2@test.com', password='123456')
        self.player_2_power = 10
        self.player_2 = Player.objects.create(
            player_name='TestPlayer2',
            player_level=10,
            player_power=self.player_2_power,
            player_life=self.player_life,
            user=self.user_2,
            player_world=self.world
        )

        self.creature_name = 'TestCreature'
        self.creature_level = 1
        self.creature_life = 100
        self.creature = WorldCreature.objects.create(
            world=self.world,
            creature_name=self.creature_name,
            creature_level=self.creature_level,
            creature_life=self.creature_life,
            creature_chance_drop=0
        )

        self.item_name_life_potion = 'TestItem'
        self.item_type_life_potion = Item.ItemType.CONSUMABLE
        self.item_power_life_potion = 100
        self.item_weight_life_potion = 10
        self.item_life_potion = Item.objects.create(
            item_name=self.item_name_life_potion,
            item_type=self.item_type_life_potion,
            item_power=self.item_power_life_potion,
            item_weight=self.item_weight_life_potion,
            item_consumable_type=Item.ItemConsumableType.LIFE
        )

        self.item_name_armour = 'TestArmour'
        self.item_type_armour = Item.ItemType.ARMOUR
        self.item_power_armour = 10
        self.item_weight_armour = 10
        self.item_armour = Item.objects.create(
            item_name=self.item_name_armour,
            item_type=self.item_type_armour,
            item_power=self.item_power_armour,
            item_weight=self.item_weight_armour
        )

        self.item_name_weapon = 'TestWeapon'
        self.item_type_weapon = Item.ItemType.WEAPON
        self.item_power_weapon = 10
        self.item_weight_weapon = 10
        self.item_weapon = Item.objects.create(
            item_name=self.item_name_weapon,
            item_type=self.item_type_weapon,
            item_power=self.item_power_weapon,
            item_weight=self.item_weight_weapon
        )

    def test_orphan_items_cleaning(self):
        self.item_armour.item_created_date = timezone.now() - timedelta(days=2)
        self.item_armour.save(update_fields=['item_created_date'])

        async_result = clean_orphan_items.delay()
        async_result.get(timeout=5)

        self.assertFalse(Item.objects.filter(id=self.item_armour.id).exists())
        self.assertTrue(async_result.successful())

    def test_tick__respawn_creatures__recover_player_status(self):
        total_creatures = WorldCreature.objects.filter(
            world=self.world
        ).count()
        self.player.player_life = 50
        self.player.player_stamina = 50
        self.player.save(update_fields=['player_life', 'player_stamina'])

        self.assertEqual(total_creatures, 1)
        
        async_result = respawn_creatures.delay()
        async_result.get(timeout=5)

        async_result = recover_player_status.delay()
        async_result.get(timeout=5)

        total_creatures = WorldCreature.objects.filter(
            world=self.world
        ).count()

        self.player.refresh_from_db()
        self.assertEqual(total_creatures, 2)
        self.assertGreater(self.player.player_life, 50)
        self.assertGreater(self.player.player_stamina, 50)
        self.assertTrue(async_result.successful())

    @patch('mmo.tasks.task_fight.async_to_sync')
    @patch('mmo.tasks.task_fight.get_channel_layer')
    def test_monster_attack(self, mock_get_channel_layer, mock_async_to_sync):
        fs = FightEngine.should_fight(self.player.id)
        self.assertIsNotNone(fs)

        cl = mock_get_channel_layer.return_value        
        self.player.player_life = 1
        self.player.save(update_fields=['player_life'])

        async_result = monster_attack.apply_async(
            args=[fs.fight_id, 'test-worker'], 
            countdown=1
        )
        async_result.get(timeout=5)

        mock_async_to_sync.assert_called_once()
        mock_async_to_sync.assert_called_once_with(
            cl.send
        )
        mock_async_to_sync.return_value.assert_called_once()

        self.player.refresh_from_db()
        self.assertEqual(self.player.player_status, Player.PlayerStatus.DEAD)

    def test_clean_matchmaking_fight_timeout(self):
        with (
            patch('mmo.services.fight_engine.random.randint', return_value=1)
        ):
            cache.set(USER_CHANNEL_WS_LOGGED.format(user_id=self.user.id), 'test_channel', timeout=10)
            cache.set(USER_CHANNEL_WS_LOGGED.format(user_id=self.user_2.id), 'test_channel', timeout=10)

            fs = FightEngine.should_fight(self.player.id)
            self.assertIsNotNone(fs)
            self.assertIsNotNone(fs.opponent) #pyright: ignore

            f = Fight.objects.select_related('player', 'opponent').filter(id=fs.fight_id).first() #pyright: ignore
            p = f.player
            o = f.opponent
            self.assertIsNotNone(f)
            self.assertIsNotNone(p)
            self.assertIsNotNone(o)
            
            async_result = clean_up_matchmaking_fight.delay(fs.fight_id) #pyright: ignore
            async_result.get(timeout=5)

            self.assertFalse(Fight.objects.filter(id=fs.fight_id).exists()) #pyright: ignore

    def test_clean_matchmaking_fight_in_fight(self):
        with (
            patch('mmo.services.fight_engine.random.randint', return_value=1)
        ):
            cache.set(USER_CHANNEL_WS_LOGGED.format(user_id=self.user.id), 'test_channel', timeout=10)
            cache.set(USER_CHANNEL_WS_LOGGED.format(user_id=self.user_2.id), 'test_channel', timeout=10)

            fs = FightEngine.should_fight(self.player.id)
            self.assertIsNotNone(fs)
            self.assertIsNotNone(fs.opponent) #pyright: ignore

            f = Fight.objects.select_related('player', 'opponent').filter(id=fs.fight_id).first() #pyright: ignore
            p = f.player
            o = f.opponent
            self.assertIsNotNone(f)
            self.assertIsNotNone(p)
            self.assertIsNotNone(o)
            
            cache.add(MATCHMAKING_IN_FIGHT.format(fight_id=fs.fight_id), True, timeout=10)

            async_result = clean_up_matchmaking_fight.delay(fs.fight_id) #pyright: ignore
            async_result.get(timeout=5)

            self.assertTrue(Fight.objects.filter(id=fs.fight_id).exists()) #pyright: ignore

    def test_player_death_penalty(self):
        self.player.player_status = Player.PlayerStatus.DEAD
        self.player.player_exp = 1000
        inv_armour = PlayerInventory.objects.create(
            item=self.item_armour,
            player=self.player
        )
        inv_weapon = PlayerInventory.objects.create(
            item=self.item_weapon,
            player=self.player
        )
        self.player.player_equipped_armour = inv_armour
        self.player.player_equipped_weapon = inv_weapon

        self.player.save(update_fields=[
            'player_status', 'player_currency', 
            'player_equipped_armour', 'player_equipped_weapon'
        ])

        async_result = apply_death_penalty_to_player.delay(self.player.id)
        async_result.get(timeout=5)

        self.player.refresh_from_db()
        self.assertEqual(self.player.player_status, Player.PlayerStatus.DEAD)
        self.assertEqual(self.player.player_currency, 0)
        self.assertIsNone(self.player.player_equipped_armour)
        self.assertIsNone(self.player.player_equipped_weapon)

    def test_revive_dead_player(self):
        self.player.player_status = Player.PlayerStatus.DEAD
        self.player.save(update_fields=['player_status'])

        cache.add(
            USER_CHANNEL_WS_LOGGED.format(user_id=self.user.id),
            'channel_test',
            timeout=10
        )
        async_result = revive_dead_players.delay()
        async_result.get(timeout=5)

        self.player.refresh_from_db()
        self.assertEqual(self.player.player_status, Player.PlayerStatus.IDLE)
