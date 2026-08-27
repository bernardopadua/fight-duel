from django.contrib.auth.models import User

from django.test import TestCase

from unittest.mock import MagicMock, patch

from rest_framework.test import APITestCase
from rest_framework import status

from mmo.services.fight_engine import FightEngine, FightStart
from mmo.services.player_inventory_engine import PlayerInventoryEngine
from mmo.models import Player, World, WorldCreature, Fight, Item

class MMOPlayerTests(APITestCase):
    
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='test', email='test@test.com', password='123456')
        self.client.force_authenticate(user=self.user)

    def test_create_new_player(self):
        response = self.client.post(
            '/api/mmo/create/player/', 
            {'playerName': 'NewPlayer'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("playerName", response.json())

    def test_create_duplicated_player(self):
        response = self.client.post(
            '/api/mmo/create/player/', 
            {'playerName': 'NewPlayer'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("playerName", response.json())

        response = self.client.post(
            '/api/mmo/create/player/', 
            {'playerName': 'NewPlayer'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("playerName", response.json())

    def test_get_player(self):
        Player.objects.create(
            user=self.user,
            player_name='TestPlayer',
            player_level=10
        )
        response = self.client.get(
            '/api/mmo/player/', 
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("playerName", response.json())
        self.assertEqual(response.json()['playerName'], 'TestPlayer')
        self.assertEqual(response.json()['playerLevel'], 10)

class MMOPlayerFightTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='test', email='test@test.com', password='123456')
        self.player_life = 100
        self.player = Player.objects.create(
            player_name='TestPlayer',
            player_level=10,
            player_power=100,
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
            creature_chance_drop=100
        )

        self.item_name_life_potion = "TestItem"
        self.item_type_life_potion = Item.ItemType.CONSUMABLE
        self.item_power_life_potion = 10
        self.item_weight_life_potion = 10
        self.item_life_potion = Item.objects.create(
            item_name=self.item_name_life_potion,
            item_type=self.item_type_life_potion,
            item_power=self.item_power_life_potion,
            item_weight=self.item_weight_life_potion,
            item_consumable_type=Item.ItemConsumableType.LIFE
        )

        self.item_name_armour = "TestArmour"
        self.item_type_armour = Item.ItemType.ARMOUR
        self.item_power_armour = 10
        self.item_weight_armour = 10
        self.item_armour = Item.objects.create(
            item_name=self.item_name_armour,
            item_type=self.item_type_armour,
            item_power=self.item_power_armour,
            item_weight=self.item_weight_armour
        )

        self.item_name_weapon = "TestWeapon"
        self.item_type_weapon = Item.ItemType.WEAPON
        self.item_power_weapon = 10
        self.item_weight_weapon = 10
        self.item_weapon = Item.objects.create(
            item_name=self.item_name_weapon,
            item_type=self.item_type_weapon,
            item_power=self.item_power_weapon,
            item_weight=self.item_weight_weapon
        )

    def _should_fight(self) -> FightStart:
        fs = FightEngine.should_fight(self.player.id)
        
        f = Fight.objects.filter(id=fs.fight_id)
        self.assertEqual(f.count(), 1)
        self.assertIsNotNone(f.first())

        return fs

    def test_fight_move_start(self):
        fs = FightEngine.should_fight(self.player.id)
        self.assertIsNotNone(fs)
        self.assertEqual(fs.creature_name, self.creature_name)
        self.assertEqual(fs.creature_level, self.creature_level)

        fight = Fight.objects.filter(id=fs.fight_id)
        self.assertEqual(fight.count(), 1)
        self.assertEqual(fs.fight_id, fight.first().id)
        
    def test_fight_attack_monster(self):
        fs = self._should_fight()
        
        self.player.refresh_from_db()
        self.assertEqual(self.player.player_status, Player.PlayerStatus.FIGHTING)

        fst = FightEngine.attack_monster(fs.fight_id)
        self.assertIsNotNone(fst)
        self.assertEqual(fst.player_life, self.player_life)
        self.assertTrue(fst.creature_life < self.creature_life)

    def test_fight_player_flee(self):
        fs = self._should_fight()
        
        FightEngine.player_flee(fs.fight_id)

        f = Fight.objects.filter(id=fs.fight_id)
        self.assertEqual(f.count(), 0)
        self.assertIsNone(f.first())

        self.player.refresh_from_db()
        self.assertEqual(self.player.player_status, Player.PlayerStatus.IDLE)
        
    def test_attack_player(self):
        fs = self._should_fight()
        
        fst = FightEngine.attack_player(fs.fight_id)

        self.assertIsNotNone(fst)
        self.assertEqual(self.creature_life, fst.creature_life)
        self.assertTrue(fst.player_life < self.player_life)

    @patch('mmo.services.fight_engine.DropEngine.drop_items')
    @patch('mmo.services.fight_engine.get_channel_layer')
    @patch('mmo.services.fight_engine.async_to_sync')
    def test_monster_die_and_drop(self, mock_async_to_sync, mock_chanel_layer, mock_drop_items):
        fs = self._should_fight()

        mock_drop_items.return_value = ([self.item_armour], 150)

        #one hit kill
        self.player.player_power = 99999
        self.player.save(update_fields=['player_power'])

        fst = FightEngine.attack_monster(fs.fight_id)
        self.assertIsNotNone(fst)
        self.assertTrue(fst.is_fight_over)
        self.assertTrue(fst.is_player_alive)
        self.assertFalse(fst.is_monster_alive)
        self.assertEqual(fst.player_life, self.player_life)
        self.assertEqual(fst.creature_life, 0)
        
        mock_drop_items.assert_called_once()
        mock_chanel_layer.assert_called_once()
        mock_async_to_sync.assert_called_with(mock_chanel_layer.return_value.group_send)

        self.assertFalse(WorldCreature.objects.filter(id=self.creature.id).exists())
        self.assertFalse(Fight.objects.filter(id=fs.fight_id).exists())

        self.player.refresh_from_db()
        self.assertEqual(self.player.player_status, Player.PlayerStatus.IDLE)
        self.assertEqual(self.player.player_currency, 150)
        self.assertEqual(self.player.player_level, 10)

    def test_player_die_and_loot_item_player_inventory_engine(self):
        fs = self._should_fight()

        #one hit kill player
        self.creature.creature_level = 99999
        self.creature.save(update_fields=['creature_level'])

        #testing player penalty on death
        looted = PlayerInventoryEngine.loot_items(self.player.id, [self.item_armour.id, self.item_weapon.id])
        self.assertTrue(looted)
        self.player.refresh_from_db()
        
        items = PlayerInventoryEngine.get_player_inventory(self.player.id)
        self.assertTrue(len(items) == 2)
        self.assertIn("itemName", items[0])
        self.assertDictEqual(items[0], self.item_armour.to_dict())

        fst = FightEngine.attack_player(fs.fight_id)
        self.assertIsNotNone(fst)
        self.assertFalse(fst.is_player_alive)
        self.assertTrue(fst.is_monster_alive)
        self.assertEqual(fst.player_life, 0)
        self.assertEqual(fst.creature_life, self.creature_life)

        f = Fight.objects.filter(id=fs.fight_id)
        self.assertEqual(f.count(), 0)
        self.assertIsNone(f.first())

        #is dead and no items equiped 
        self.player.refresh_from_db()
        self.assertEqual(self.player.player_status, Player.PlayerStatus.DEAD)
        self.assertIsNone(self.player.player_equipped_armour)
        self.assertIsNone(self.player.player_equipped_weapon)
        self.assertEqual(self.player.player_level, 10)
        self.assertEqual(self.player.player_exp, 0)

