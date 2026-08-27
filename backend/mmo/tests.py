from asgiref.sync import async_to_sync, sync_to_async
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase, override_settings
from django.conf import settings

from unittest.mock import patch

from rest_framework.test import APITestCase
from rest_framework import status

from channels.testing import WebsocketCommunicator
from core.asgi import application

from mmo.consumers import ToClientActions, ToServerActions
from mmo.services.fight_engine import FightEngine, FightStart
from mmo.services.player_engine import PlayerEngine
from mmo.services.player_inventory_engine import PlayerInventoryEngine
from mmo.models import Player, World, WorldCreature, Fight, Item

from fkdauth.jwt_auth_utils import create_token

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

@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
class GameConsumerTests(TransactionTestCase):
    def setUp(self) -> None:
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

    async def _connect_to_websocket(self) -> WebsocketCommunicator:
        token_headers = [
            (b'cookie', f'Authorization-JWT={self.token}'.encode()),
        ]
        communicator = WebsocketCommunicator(
            application, '/ws/fight/',
            headers=token_headers
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        self.addCleanup(async_to_sync(communicator.disconnect))

        return communicator

    async def test_connect_without_token_error(self):
        pass

    @patch('mmo.consumers.monster_attack.apply_async')
    async def test_websocket_move_and_fight(self, mock_monster_attack):
        communicator = await self._connect_to_websocket()

        await communicator.send_json_to({'action': ToServerActions.MOVE})
        response = await communicator.receive_json_from()

        self.assertEqual(response['action'], ToClientActions.FIGHT)
        self.assertIn('data', response)
        self.assertIn('fightId', response['data'])
        self.assertIsNotNone(response['data']['fightId'])
        
        mock_monster_attack.assert_called_once() 
        channel_name = mock_monster_attack.call_args.kwargs['args'][1]

        fight_id = response['data']['fightId']

        #monster attack
        from mmo.tasks import monster_attack
        await sync_to_async(monster_attack)(fight_id, channel_name)

        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.FIGHT_UPDATE)
        self.assertIn('data', response)
        self.assertIn('isPlayerAlive', response['data'])
        self.assertIn('isMonsterAlive', response['data'])
        self.assertTrue(response['data']['isPlayerAlive'])
        self.assertTrue(response['data']['isMonsterAlive'])
        
        await communicator.send_json_to({'action': ToServerActions.ATTACK})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.FIGHT_UPDATE)
        self.assertIn('data', response)
        self.assertIn('isPlayerAlive', response['data'])
        self.assertIn('isMonsterAlive', response['data'])
        self.assertTrue(response['data']['isPlayerAlive'])
        self.assertFalse(response['data']['isMonsterAlive'])

        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], 'fight.finish')
        self.assertIn('data', response)
        self.assertIn('isFightOver', response['data'])
        self.assertTrue(response['data']['isFightOver'])

        await communicator.disconnect()
    
    @patch('mmo.services.fight_engine.DropEngine.drop_items')
    @patch('mmo.consumers.monster_attack.apply_async')
    async def test_websocket_move_and_fight_loot_item(self, mock_monster_attack, mock_drop_items):
        self.creature.creature_chance_drop = 100
        await sync_to_async(self.creature.save)(update_fields=['creature_chance_drop'])

        communicator = await self._connect_to_websocket()

        await communicator.send_json_to({'action': ToServerActions.MOVE})
        response = await communicator.receive_json_from()

        self.assertEqual(response['action'], ToClientActions.FIGHT)
        self.assertIn('data', response)
        self.assertIn('fightId', response['data'])
        self.assertIsNotNone(response['data']['fightId'])
        
        mock_monster_attack.assert_called_once() 
        channel_name = mock_monster_attack.call_args.kwargs['args'][1]

        fight_id = response['data']['fightId']

        #monster attack
        from mmo.tasks import monster_attack
        await sync_to_async(monster_attack)(fight_id, channel_name)

        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.FIGHT_UPDATE)
        self.assertIn('data', response)
        self.assertIn('isPlayerAlive', response['data'])
        self.assertIn('isMonsterAlive', response['data'])
        self.assertTrue(response['data']['isPlayerAlive'])
        self.assertTrue(response['data']['isMonsterAlive'])
        
        mock_drop_items.return_value = ([self.item_armour, self.item_weapon], 100)
        items_drop_ids = [self.item_armour.id, self.item_weapon.id]

        await communicator.send_json_to({'action': ToServerActions.ATTACK})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.FIGHT_UPDATE)
        self.assertIn('data', response)
        self.assertIn('isPlayerAlive', response['data'])
        self.assertIn('isMonsterAlive', response['data'])
        self.assertTrue(response['data']['isPlayerAlive'])
        self.assertFalse(response['data']['isMonsterAlive'])

        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.FIGHT_DROP_ITEMS)
        self.assertIn('data', response)
        self.assertTrue(len(response['data']) > 0)
        self.assertEqual(len(response['data']), 2)
        
        loot_items = response['data']
        for item in loot_items:
            self.assertIn('id', item)
            self.assertIn('itemName', item)
            self.assertIn('itemType', item)
            self.assertIn('itemPower', item)
            self.assertIn('itemWeight', item)
            self.assertIn('itemConsumableType', item)
            self.assertIn(item['id'], items_drop_ids)

        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.FIGHT_FINISH)
        self.assertIn('data', response)
        self.assertIn('isFightOver', response['data'])
        self.assertTrue(response['data']['isFightOver'])

        await communicator.send_json_to({'action': ToServerActions.LOOT, 'data': items_drop_ids})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.INVENTORY_UPDATE)
        self.assertIn('data', response)
        self.assertIsInstance(response['data'], list)
        for item in response['data']:
            self.assertIn('itemName', item)
            self.assertIn('id', item)
            self.assertIn(item['itemName'], [self.item_armour.item_name, self.item_weapon.item_name])

        await communicator.disconnect()

    #flee
    async def test_websocket_move_and_flee(self):
        communicator = await self._connect_to_websocket()

        await communicator.send_json_to({'action': ToServerActions.MOVE})
        response = await communicator.receive_json_from()

        self.assertEqual(response['action'], ToClientActions.FIGHT)
        self.assertIn('data', response)
        self.assertIn('fightId', response['data'])
        self.assertIsNotNone(response['data']['fightId'])
        
        await communicator.send_json_to({'action': ToServerActions.FLEE})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.FIGHT_FINISH)
        self.assertIn('data', response)
        self.assertIn('isFightOver', response['data'])
        self.assertTrue(response['data']['isFightOver'])

        await self.player.arefresh_from_db()
        self.assertEqual(await Fight.objects.all().acount(), 0)
        self.assertEqual(self.player.player_status, Player.PlayerStatus.IDLE)

        await communicator.disconnect()

    #use_item
    async def test_websocket_move_and_use_item(self):
        from mmo.services.constants import LEVELUP_PLUS_PLAYERPOWER
        communicator = await self._connect_to_websocket()
        self.player.player_life = 60
        self.player.player_power = 10 + (10*LEVELUP_PLUS_PLAYERPOWER)
        await self.player.asave(update_fields=['player_life', 'player_power'])

        looted_items = await sync_to_async(PlayerInventoryEngine.loot_items)(self.player.id, [self.item_life_potion.id])
        self.assertTrue(looted_items)

        await communicator.send_json_to({'action': ToServerActions.GET_INVENTORY})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.INVENTORY_UPDATE)
        self.assertIn('data', response)
        self.assertIsInstance(response['data'], list)
        self.assertEqual(len(response['data']), 1)
        self.assertEqual(response['data'][0]['itemName'], self.item_life_potion.item_name)
        self.assertEqual(response['data'][0]['id'], self.item_life_potion.id)

        await communicator.send_json_to({'action': ToServerActions.USE_ITEM, 'data': self.item_life_potion.id})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.INVENTORY_UPDATE)
        self.assertIn('data', response)
        self.assertIsInstance(response['data'], list)
        self.assertEqual(len(response['data']), 0)

        await self.player.arefresh_from_db()
        self.assertEqual(self.player.player_life, await sync_to_async(PlayerEngine.get_player_calculated_life)(self.player))

        await communicator.disconnect()