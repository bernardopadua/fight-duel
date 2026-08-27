from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User

from unittest.mock import patch, ANY

from fkdauth.jwt_auth_utils import create_token

from mmo.models import World, Player, WorldCreature, Item, Fight
from mmo.services.fight_engine import FightEngine, FightStart
from mmo.tasks import monster_attack, respawn_creatures, recover_player_status, tick, clean_orphan_items

from django.utils import timezone
from datetime import timedelta

class MMOTasksTests(TestCase):
    def setUp(self) -> None:
        #I decided to copy instead of doing a unique class with this scope under.
        self.user = User.objects.create_user(username='test', email='test@test.com', password='123456')
        self.token = create_token(self.user.id, settings.SECRET_KEY)

        self.player_power = 999
        self.player_life = 100
        self.player = Player.objects.create(
            player_name='TestPlayer',
            player_level=10,
            player_power=self.player_power,
            player_life=self.player_life,
            user=self.user
        )
        self.world = World.objects.create(
            world_name='TestWorld',
            world_total_creatures=2,
            world_min_level=1,
            world_max_level=10
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

        self.item_name_armour_2 = 'TestArmour2'
        self.item_type_armour_2 = Item.ItemType.ARMOUR
        self.item_power_armour_2 = 10
        self.item_weight_armour_2 = 10
        self.item_armour_2 = Item.objects.create(
            item_name=self.item_name_armour_2,
            item_type=self.item_type_armour_2,
            item_power=self.item_power_armour_2,
            item_weight=self.item_weight_armour_2
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

    def _setup_fight(self) -> FightStart:
        fs = FightEngine.should_fight(self.player.id)
        self.assertIsNotNone(fs) #<<
        f = Fight.objects.filter(id=fs.fight_id).first() #pyright: ignore
        self.assertIsNotNone(f)

        return fs #pyright: ignore

    @patch('mmo.tasks.get_channel_layer')
    @patch('mmo.tasks.monster_attack.apply_async')
    @patch('mmo.tasks.async_to_sync')
    def test_monster_attack(self, mock_async_to_sync, mock_apply_async, mock_get_channel_layer):
        fs = self._setup_fight()

        monster_attack(fs.fight_id, 'channel-test')

        cl = mock_get_channel_layer.return_value

        mock_apply_async.assert_called_once_with(args=[fs.fight_id, 'channel-test'], countdown=ANY)
        mock_async_to_sync.assert_called_once_with(cl.send)
        cl = mock_async_to_sync.return_value
        mock_async_to_sync.return_value.assert_called_once()

        call_args, _ = cl.call_args
        self.assertEqual(call_args[0], 'channel-test')
        self.assertEqual(call_args[1]['type'], "fight.update")
        #TODO: ellaborate these asserts. as the game "grows" if it becomes more complex.
        self.assertEqual(call_args[1]['data']['creatureLevel'], self.creature_level)

    def test_respawn_monsters(self):
        total_monsters = WorldCreature.objects.filter(
            world=self.world
        ).count()

        self.assertEqual(total_monsters, 1)

        respawn_creatures()
        
        total_monsters = WorldCreature.objects.filter(
            world=self.world
        ).count()

        self.assertEqual(total_monsters, 2)       

    @patch('mmo.tasks.PlayerEngine.recover_players_status')
    def test_recover_player_status(self, mock_recover_players_status):
        fs = FightEngine.should_fight(self.player.id)
        self.assertIsNotNone(fs) # <<<<
        f = Fight.objects.filter(id=fs.fight_id).first() #pyright: ignore
        self.assertIsNotNone(f)

        recover_player_status()

        mock_recover_players_status.assert_not_called()

        FightEngine.player_flee(fs.fight_id) #pyright: ignore
        
        recover_player_status()
        
        mock_recover_players_status.assert_called_once()

    def test_recover_player_status_low_life(self):
        self.player.player_life = 50
        self.player.player_stamina = 50
        self.player.save(update_fields=['player_life', 'player_stamina'])

        recover_player_status()

        self.player.refresh_from_db()
        self.assertGreater(self.player.player_life, 50)
        self.assertGreater(self.player.player_stamina, 50)

    @patch('mmo.tasks.respawn_creatures.delay')
    @patch('mmo.tasks.recover_player_status.delay')
    def test_cron_tasks(self, mock_recover_player_status, mock_respawn_creatures):
        tick()

        mock_recover_player_status.assert_called_once()
        mock_respawn_creatures.assert_called_once()
    
    def test_clean_orphan_items_delete_item(self):
        self.item_armour.item_created_date = timezone.now() - timedelta(days=2)
        self.item_armour.save(update_fields=['item_created_date'])

        clean_orphan_items()

        item_deleted = Item.objects.filter(
            id=self.item_armour.id
        ).first()

        self.assertIsNone(item_deleted)

    def test_clean_orphan_items_not_delete_item(self):
        self.item_armour.item_created_date = timezone.now() - timedelta(hours=1)
        self.item_armour.save(update_fields=['item_created_date'])

        clean_orphan_items()

        item_deleted = Item.objects.filter(
            id=self.item_armour.id
        ).first()

        self.assertIsNotNone(item_deleted)