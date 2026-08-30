from unittest.mock import patch

from celery.contrib.testing.worker import start_worker

from django.contrib.auth.models import User
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from core.settings import CELERY_REDIS_HOST_DB
from core.celery import app

from core.settings import CELERY_RESULT_BACKEND
from mmo.models import Item, Player, World, WorldCreature
from mmo.services.fight_engine import FightEngine
from mmo.tasks import clean_orphan_items, respawn_creatures, recover_player_status, monster_attack

from datetime import timedelta

# @override_settings(
#     CELERY_RESULT_BACKEND=CELERY_REDIS_HOST_DB.format(db='15'),
#     CELERY_BROKER_URL=CELERY_REDIS_HOST_DB.format(db='15')
# )
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

    @patch('mmo.tasks.async_to_sync')
    @patch('mmo.tasks.get_channel_layer')
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

