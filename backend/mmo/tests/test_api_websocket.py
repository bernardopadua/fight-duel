from asgiref.sync import async_to_sync, sync_to_async
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase, override_settings
from django.conf import settings
from django.core.cache import cache

from unittest.mock import patch

from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from channels.testing import WebsocketCommunicator
from core.asgi import application

from mmo.consumers import ToClientActions, ToServerActions
from mmo.services.drop_engine import DropEngine
from mmo.services.fight_engine import FightEngine, FightStart
from mmo.services.player_engine import PlayerEngine
from mmo.services.world_engine import WorldEngine
from mmo.services.player_inventory_engine import PlayerInventoryEngine
from mmo.models import Player, PlayerInventory, World, WorldCreature, Fight, Item
from mmo.constants import USER_CHANNEL_WS_LOGGED

from fkdauth.jwt_auth_utils import create_token

class MMOPlayerTests(APITestCase):
    
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='test', email='test@test.com', password='123456')
        self.client.force_authenticate(user=self.user)
        self.anonymous_client = APIClient()

    def test_create_new_player_not_logged_in(self):
        response = self.anonymous_client.post(
            '/api/mmo/create/player/', 
            {'playerName': 'NewPlayer'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_player_not_logged_in(self):
        response = self.anonymous_client.get('/api/mmo/player/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

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

    def test_get_player_with_equipped_items(self):
        response = self.client.post(
            '/api/mmo/create/player/', 
            {'playerName': 'NewPlayer'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        player_id = response.json()['id']
        self.assertIsNotNone(player_id)

        itemd = DropEngine.create_drop_item(10, item_type=Item.ItemType.ARMOUR)
        PlayerInventoryEngine.loot_items(player_id, [itemd.id])
        PlayerInventoryEngine.use_item(player_id, itemd.id)
        
        response = self.client.get(
            '/api/mmo/player/', 
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("playerEquippedWeaponItem", response.json())
        self.assertIn("playerEquippedArmourItem", response.json())
        self.assertIsNotNone(response.json())
        self.assertIsNotNone(response.json()['playerEquippedArmourItem'])
        self.assertIsNone(response.json()['playerEquippedWeaponItem'])
        self.assertIn('itemName', response.json()['playerEquippedArmourItem'])
        self.assertIn('itemWeight', response.json()['playerEquippedArmourItem'])
        self.assertIn('itemPower', response.json()['playerEquippedArmourItem'])

class MMOWorldTests(TestCase):
    def setUp(self) -> None:
        cache.clear()

        self.world = World.objects.create(
            world_name='TestWorld',
            world_total_creatures=2,
            world_min_level=1,
            world_max_level=10
        )
        self.world_2 = World.objects.create(
            world_name='TestWorld2',
            world_total_creatures=2,
            world_min_level=1,
            world_max_level=10
        )

        self.user = User.objects.create_user(username='test', email='test@test.com', password='123456')
        self.token = create_token(self.user.id, settings.SECRET_KEY)
        self.player_life = 100
        self.player = Player.objects.create(
            player_name='TestPlayer',
            player_level=10,
            player_power=100,
            player_life=self.player_life,
            user=self.user,
            player_world=self.world
        )

    def test_get_worlds(self):
        response = self.client.get(
            '/api/mmo/worlds/',
            HTTP_AUTHORIZATION=f'Bearer {self.token}',
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(len(response.json()), 2)
        self.assertIn('worldName', response.json()[0])
        self.assertIn('worldMinLevel', response.json()[0])
        self.assertIn('worldMaxLevel', response.json()[0])

@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "game-fight-engine-tests"
        }
    }
)
class MMOPlayerFightTests(TestCase):
    def setUp(self) -> None:
        cache.clear()

        self.world = World.objects.create(
            world_name='TestWorld',
            world_total_creatures=2,
            world_min_level=1,
            world_max_level=10
        )
        
        self.world_2 = World.objects.create(
            world_name='TestWorld2',
            world_total_creatures=2,
            world_min_level=10,
            world_max_level=20
        )

        self.user = User.objects.create_user(username='test', email='test@test.com', password='123456')
        self.player_life = 100
        self.player = Player.objects.create(
            player_name='TestPlayer',
            player_level=10,
            player_power=100,
            player_life=self.player_life,
            user=self.user,
            player_world=self.world
        )

        self.user_2 = User.objects.create_user(username='test_2', email='test_2@test.com', password='123456')
        self.player_life_2 = 100
        self.player_2 = Player.objects.create(
            player_name='TestPlayer_2',
            player_level=10,
            player_power=100,
            player_life=self.player_life_2,
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

    def test_fight_should_not_fight_player_is_not_in_world(self):
        self.player.player_world = None
        self.player.save(update_fields=['player_world'])

        fs = FightEngine.should_fight(self.player.id)
        self.assertIsNone(fs)
    
    def test_fight_should_not_fight_player_is_dead(self):
        self.player.player_life = 0
        self.player.player_status = Player.PlayerStatus.DEAD
        self.player.save(update_fields=['player_life','player_status'])

        fs = FightEngine.should_fight(self.player.id)
        self.assertIsNone(fs)

    def test_fight_should_not_fight_player_is_fighting(self):
        self.player.player_status = Player.PlayerStatus.FIGHTING
        self.player.save(update_fields=['player_status'])

        fs = FightEngine.should_fight(self.player.id)
        self.assertIsNone(fs)

    def test_fight_cant_enter_world_high_level(self):
        self.player.player_level = 20
        self.player.player_world = None
        self.player.save(update_fields=['player_level', 'player_world'])

        result = WorldEngine.enter_world(self.player.id, self.world.id)
        self.assertIsNone(result)

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
        
        FightEngine.player_flee(fs.fight_id, self.player.id)

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
        self.player.player_power = 999
        self.player.player_stamina = 99999
        self.player.save(update_fields=['player_power', 'player_stamina'])

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

@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}},
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "game-consumer-tests"
        }
    }
)
class MMOConsumerTests(TransactionTestCase):
    """
        This test takes in consideration the client side thats why some messages are silent.
        But in the future I will rework this or not, I don't know yet.
    """
    def setUp(self) -> None:
        cache.clear()

        self.user = User.objects.create_user(username='test', email='test@test.com', password='123456')
        self.token = create_token(self.user.id, settings.SECRET_KEY)

        self.world = World.objects.create(
            world_name='TestWorld',
            world_total_creatures=2,
            world_min_level=1,
            world_max_level=10
        )

        self.world_2 = World.objects.create(
            world_name='TestWorld2',
            world_total_creatures=2,
            world_min_level=10,
            world_max_level=20
        )

        self.player_power = 999
        self.player_stamina = 9999
        self.player_life = 100
        self.player = Player.objects.create(
            player_name='TestPlayer',
            player_level=10,
            player_power=self.player_power,
            player_life=self.player_life,
            player_stamina=self.player_stamina,
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

    async def _safe_disconnect(self, communicator: WebsocketCommunicator) -> None:
        try:
            await communicator.disconnect()
        except Exception:
            pass

    async def _connect_to_websocket(self, 
        *,
        test_expired_connection: bool = False,
        test_connected_false: bool = False
    ) -> WebsocketCommunicator:
        token_headers = [
            (b'cookie', f'Authorization-JWT={self.token}'.encode()),
        ]
        communicator = WebsocketCommunicator(
            application, '/ws/fight/',
            headers=token_headers
        )
        connected, _ = await communicator.connect()

        if test_expired_connection:
            self.assertFalse(connected)    
            return communicator

        if test_connected_false:
            self.assertFalse(connected)    
            return communicator

        self.assertTrue(connected)
        self.addCleanup(async_to_sync(self._safe_disconnect), communicator)

        return communicator

    async def test_websocket_expired_token_connect(self):
        self.token = create_token(self.user.id, settings.SECRET_KEY, time_expires=-1)
        communicator = await self._connect_to_websocket(test_expired_connection=True)

    async def test_websocket_invalid_payload(self):
        communicator = await self._connect_to_websocket()
        
        await communicator.send_to("unknown payload")
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.ERROR)
        self.assertEqual(response['data'], "Invalid JSON")

        close_event = await communicator.receive_output()
        self.assertEqual(close_event["type"], "websocket.close")

        await communicator.disconnect()

    async def test_websocket_connect_without_token_error(self):
        communicator = WebsocketCommunicator(
            application, '/ws/fight/',
            headers=[]
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_websocket_connect_with_invalid_token(self):
        token_headers = [
            (b'cookie', f'Authorization-JWT=invalid.token.invalid'.encode()),
        ]
        communicator = WebsocketCommunicator(
            application, '/ws/fight/',
            headers=token_headers
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_websocket_sudden_disconnect_player(self):
        communicator = await self._connect_to_websocket()

        await communicator.send_json_to({'action': ToServerActions.MOVE})
        response = await communicator.receive_json_from()

        self.assertEqual(response['action'], ToClientActions.FIGHT)
        self.assertIn('data', response)
        self.assertIn('fightId', response['data'])
        self.assertIsNotNone(response['data']['fightId'])

        fight_id = response['data']['fightId']

        await communicator.disconnect()

        f = Fight.objects.filter(id=fight_id)
        p = Player.objects.filter(id=self.player.id)
        fight = await f.afirst()
        player = await p.afirst()
        self.assertIsNone(fight)
        self.assertIsNotNone(player) # <<<
        self.assertEqual(player.player_status, Player.PlayerStatus.IDLE) # pyright: ignore

    async def test_websocket_move_and_fight_without_world(self):
        self.player.player_world = None
        await self.player.asave(update_fields=['player_world'])

        communicator = await self._connect_to_websocket()

        await communicator.send_json_to({'action': ToServerActions.MOVE})
        self.assertTrue(await communicator.receive_nothing())
        self.assertFalse(await sync_to_async(FightEngine.is_player_in_a_fight)(self.player.id))

        await communicator.disconnect()

    async def test_websocket_enter_in_world(self):
        self.player.player_world = None
        await self.player.asave(update_fields=['player_world'])

        communicator = await self._connect_to_websocket()

        await communicator.send_json_to({'action': ToServerActions.ENTER_WORLD, 'data': self.world.id})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.WORLD_ENTER)
        self.assertIn('data', response)
        self.assertIn('id', response['data'])
        self.assertIsNotNone(response['data']['id'])
        self.assertEqual(response['data']['id'], self.world.id)
        self.assertEqual(response['data']['worldName'], self.world.world_name)

        await communicator.disconnect()

    async def test_websocket_change_world_after_entering(self):
        communicator = await self._connect_to_websocket()

        await communicator.send_json_to({'action': ToServerActions.ENTER_WORLD, 'data': self.world.id})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.WORLD_ENTER)
        self.assertIn('data', response)
        self.assertIn('id', response['data'])
        self.assertIsNotNone(response['data']['id'])
        self.assertEqual(response['data']['id'], self.world.id)
        self.assertEqual(response['data']['worldName'], self.world.world_name)

        await communicator.send_json_to({'action': ToServerActions.CHANGE_WORLD, 'data': self.world_2.id})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.WORLD_ENTER)
        self.assertIn('data', response)
        self.assertIn('id', response['data'])
        self.assertIsNotNone(response['data']['id'])
        self.assertEqual(response['data']['id'], self.world_2.id)
        self.assertEqual(response['data']['worldName'], self.world_2.world_name)

        await communicator.disconnect()

    async def test_websocket_enter_world_rejected_due_to_world_max_level(self):
        self.player.player_level = 101
        self.player.player_world = None
        await self.player.asave(update_fields=['player_level', 'player_world'])

        communicator = await self._connect_to_websocket()

        await communicator.send_json_to({'action': ToServerActions.ENTER_WORLD, 'data': self.world.id})
        self.assertTrue(await communicator.receive_nothing())

        await self.player.arefresh_from_db()
        self.assertIsNone(self.player.player_world)

        await communicator.disconnect()

    async def test_websocket_disconnect_leaves_world(self):
        communicator = await self._connect_to_websocket()
        await communicator.disconnect()
        
        await self.player.arefresh_from_db()
        self.assertIsNone(self.player.player_world)

    @patch('mmo.consumers.monster_attack.apply_async')
    async def test_attack_no_stamina(self, mock_monster_attack):
        self.player.player_power = 10
        self.player.player_stamina = 1
        await self.player.asave(update_fields=['player_power', 'player_stamina'])
        
        communicator = await self._connect_to_websocket()

        await communicator.send_json_to({'action': ToServerActions.MOVE})
        response = await communicator.receive_json_from()

        mock_monster_attack.assert_called_once()

        self.assertEqual(response['action'], ToClientActions.FIGHT)
        self.assertIn('data', response)
        self.assertIn('fightId', response['data'])
        self.assertIsNotNone(response['data']['fightId'])

        await communicator.send_json_to({'action': ToServerActions.MOVE})
        
        await communicator.send_json_to({'action': ToServerActions.ATTACK})
        self.assertTrue(await communicator.receive_nothing())

        await communicator.disconnect()

    @patch('mmo.consumers.monster_attack.apply_async')
    async def test_attack_spam(self, mock_monster_attack):
        self.player.player_power = 1
        await self.player.asave(update_fields=['player_power'])
        
        communicator = await self._connect_to_websocket()

        await communicator.send_json_to({'action': ToServerActions.MOVE})
        response = await communicator.receive_json_from()

        self.assertEqual(response['action'], ToClientActions.FIGHT)
        self.assertIn('data', response)
        self.assertIn('fightId', response['data'])
        self.assertIsNotNone(response['data']['fightId'])

        await communicator.send_json_to({'action': ToServerActions.MOVE})
        self.assertTrue(await communicator.receive_nothing())

        await communicator.send_json_to({'action': ToServerActions.ATTACK})
        response = await communicator.receive_json_from()
        self.assertIn('action', response)
        self.assertEqual(response['action'], ToClientActions.FIGHT_UPDATE)
        self.assertIn('data', response)

        await communicator.send_json_to({'action': ToServerActions.ATTACK})
        self.assertTrue(await communicator.receive_nothing())

        await communicator.send_json_to({'action': ToServerActions.ATTACK})
        self.assertTrue(await communicator.receive_nothing())

        await communicator.disconnect()

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
        from mmo.tasks.task_fight import monster_attack
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
        self.assertEqual(response['action'], ToClientActions.FIGHT_FINISH)
        self.assertIn('data', response)
        self.assertIn('isFightOver', response['data'])
        self.assertTrue(response['data']['isFightOver'])

        await communicator.disconnect()

    async def test_websocket_move_as_dead_player(self):
        self.player.player_status = Player.PlayerStatus.DEAD
        await self.player.asave(update_fields=['player_status'])

        communicator = await self._connect_to_websocket()
        
        await communicator.send_json_to({'action': ToServerActions.MOVE})
        response = await communicator.receive_json_from()

        self.assertEqual(response['action'], ToClientActions.ERROR)
        self.assertIn('data', response)
        self.assertIsNotNone(response['data'])
        self.assertIn('Player is dead', response['data'])

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
        from mmo.tasks.task_fight import monster_attack
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
        self.assertEqual(self.player.player_life, self.player.player_max_life)

        await communicator.disconnect()

    #use item wear armour
    async def test_websocket_move_and_use_item_wear_armour(self):
        communicator = await self._connect_to_websocket()
        self.player.player_life = 60
        self.player.player_power = 10
        self.player.player_level = 1
        await self.player.asave(update_fields=['player_life', 'player_power', 'player_level'])

        looted_items = await sync_to_async(PlayerInventoryEngine.loot_items)(self.player.id, [self.item_armour.id])
        self.assertTrue(looted_items)

        await communicator.send_json_to({'action': ToServerActions.GET_INVENTORY})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.INVENTORY_UPDATE)
        self.assertIn('data', response)
        self.assertIsInstance(response['data'], list)
        self.assertEqual(len(response['data']), 1)
        self.assertEqual(response['data'][0]['itemName'], self.item_armour.item_name)
        self.assertEqual(response['data'][0]['id'], self.item_armour.id)

        await communicator.send_json_to({'action': ToServerActions.USE_ITEM, 'data': self.item_armour.id})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.INVENTORY_UPDATE)
        self.assertIn('data', response)
        self.assertIsInstance(response['data'], list)
        self.assertEqual(len(response['data']), 1)
        self.assertEqual(response['data'][0]['itemName'], self.item_armour.item_name)
        self.assertEqual(response['data'][0]['id'], self.item_armour.id)

        await self.player.arefresh_from_db()
        self.assertEqual(self.player.player_power, 10)
        self.assertEqual(self.player.player_power + self.item_armour.item_power, await sync_to_async(PlayerEngine.get_player_total_power)(self.player))

        await communicator.disconnect()

    async def test_websocket_use_wear_armour_and_change_for_another_armour(self):
        communicator = await self._connect_to_websocket()

        looted_items = await sync_to_async(PlayerInventoryEngine.loot_items)(self.player.id, [self.item_armour.id])
        self.assertTrue(looted_items)

        await communicator.send_json_to({'action': ToServerActions.GET_INVENTORY})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.INVENTORY_UPDATE)
        self.assertIn('data', response)
        self.assertIsInstance(response['data'], list)
        self.assertEqual(len(response['data']), 1)
        self.assertEqual(response['data'][0]['itemName'], self.item_armour.item_name)
        self.assertEqual(response['data'][0]['id'], self.item_armour.id)

        await communicator.send_json_to({'action': ToServerActions.USE_ITEM, 'data': self.item_armour.id})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.INVENTORY_UPDATE)
        self.assertIn('data', response)
        self.assertIsInstance(response['data'], list)
        self.assertEqual(len(response['data']), 1)
        self.assertEqual(response['data'][0]['itemName'], self.item_armour.item_name)
        self.assertEqual(response['data'][0]['id'], self.item_armour.id)

        inventory = await PlayerInventory.objects.filter(
            player=self.player,
            item=self.item_armour
        ).afirst()
        await self.player.arefresh_from_db()
        self.assertEqual(inventory.id, self.player.player_equipped_armour_id) #pyright: ignore

        looted_items = await sync_to_async(PlayerInventoryEngine.loot_items)(self.player.id, [self.item_armour_2.id])
        self.assertTrue(looted_items)

        await communicator.send_json_to({'action': ToServerActions.USE_ITEM, 'data': self.item_armour_2.id})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.INVENTORY_UPDATE)
        self.assertIn('data', response)
        self.assertIsInstance(response['data'], list)
        self.assertEqual(len(response['data']), 2)

        inventory = await PlayerInventory.objects.filter(
            player=self.player,
            item=self.item_armour_2
        ).afirst()
        await self.player.arefresh_from_db()
        self.assertEqual(inventory.id, self.player.player_equipped_armour_id) #pyright: ignore

        await communicator.disconnect()

    async def test_websocket_loot_item_heavier_than_can_loot(self):
        self.item_armour_2.item_weight = 90
        await self.item_armour_2.asave(update_fields=['item_weight'])
        self.item_armour.item_weight = 50
        await self.item_armour.asave(update_fields=['item_weight'])
        communicator = await self._connect_to_websocket()

        await communicator.send_json_to({'action': ToServerActions.LOOT, 'data': [self.item_armour.id, self.item_armour_2.id]})
        self.assertTrue(await communicator.receive_nothing()) #no response because not enough capacity

        await communicator.disconnect()

    @patch('mmo.services.fight_engine.DropEngine.drop_items')
    @patch('mmo.consumers.monster_attack.apply_async')
    async def test_websocket_player_dead_by_monster(self, mock_monster_attack, mock_drop_items):
        self.player.player_life = 1
        await self.player.asave(update_fields=['player_life'])
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
        from mmo.tasks.task_fight import monster_attack
        await sync_to_async(monster_attack)(fight_id, channel_name)

        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.FIGHT_FINISH)
        self.assertIn('data', response)
        self.assertIn('isPlayerAlive', response['data'])
        self.assertIn('isMonsterAlive', response['data'])
        self.assertFalse(response['data']['isPlayerAlive'])
        self.assertTrue(response['data']['isMonsterAlive'])

        await communicator.disconnect()

    async def test_websocket_attack_no_fight_id(self):
        communicator = await self._connect_to_websocket()
        await communicator.send_json_to({'action': ToServerActions.ATTACK})
        self.assertTrue(await communicator.receive_nothing())
        await communicator.disconnect()

    async def test_websocket_flee_no_fight_id(self):
        communicator = await self._connect_to_websocket()
        await communicator.send_json_to({'action': ToServerActions.FLEE})
        self.assertTrue(await communicator.receive_nothing())
        await communicator.disconnect()

    async def test_websocket_fight_loot_empty_list_or_none_or_nonexistance(self):
        self.creature.creature_chance_drop = 100
        await self.creature.asave(update_fields=['creature_chance_drop'])

        communicator = await self._connect_to_websocket()

        await communicator.send_json_to({'action': ToServerActions.MOVE})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.FIGHT)
        self.assertIn('data', response)
        self.assertIn('fightId', response['data'])
        self.assertIsNotNone(response['data']['fightId'])

        await communicator.send_json_to({'action': ToServerActions.ATTACK})
        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.FIGHT_UPDATE)
        self.assertIn('data', response)
        self.assertIn('isFightOver', response['data'])
        self.assertTrue(response['data']['isFightOver']) #player attack power 999

        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.FIGHT_DROP_ITEMS)
        self.assertIn('data', response)
        self.assertIsInstance(response['data'], list)

        response = await communicator.receive_json_from()
        self.assertEqual(response['action'], ToClientActions.FIGHT_FINISH)
        self.assertIn('data', response)
        self.assertIn('isFightOver', response['data'])
        self.assertTrue(response['data']['isFightOver'])

        await communicator.send_json_to({'action': ToServerActions.LOOT, 'data': None})
        self.assertTrue(await communicator.receive_nothing())

        await communicator.send_json_to({'action': ToServerActions.LOOT, 'data': 123})
        self.assertTrue(await communicator.receive_nothing())

        await communicator.send_json_to({'action': ToServerActions.LOOT, 'data': [123, 456]})
        self.assertTrue(await communicator.receive_nothing())

        await communicator.disconnect()

    async def test_websocket_send_unknown_action(self):
        communicator = await self._connect_to_websocket()
        await communicator.send_json_to({'action': 'unknown'})
        self.assertTrue(await communicator.receive_nothing())
        await communicator.disconnect()

    async def test_websocket_send_use_item_with_no_data_or_random_data(self):
        communicator = await self._connect_to_websocket()
        await communicator.send_json_to({'action': ToServerActions.USE_ITEM})
        self.assertTrue(await communicator.receive_nothing())
        
        await communicator.send_json_to({'action': ToServerActions.USE_ITEM, 'data': None})
        self.assertTrue(await communicator.receive_nothing())

        await communicator.send_json_to({'action': ToServerActions.USE_ITEM, 'data': 999})
        self.assertTrue(await communicator.receive_nothing())

        await communicator.disconnect()

    async def test_login_disconnect_ws(self):
        communicator = await self._connect_to_websocket()
        
        new_client = APIClient()
        response = await sync_to_async(new_client.post)(
            '/api/auth/login/', 
            {'username': 'test', 'password': '123456'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Authorization-JWT', response.cookies)
        self.assertIn('token', response.data)

        output = await communicator.receive_output()
        self.assertEqual(output['type'], 'websocket.close')

        await communicator.disconnect()

        cache_channel = cache.get(USER_CHANNEL_WS_LOGGED.format(user_id=self.user.id))
        self.assertIsNone(cache_channel)

    async def test_logout_disconnect_ws(self):
        new_client = APIClient()
        response = await sync_to_async(new_client.post)(
            '/api/auth/login/', 
            {'username': 'test', 'password': '123456'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Authorization-JWT', response.cookies)
        self.assertIn('token', response.data)
        self.token = response.data['token']

        communicator = await self._connect_to_websocket()

        response = await sync_to_async(new_client.post)(
            '/api/auth/logout/',
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Authorization-JWT', response.cookies)
        self.assertIn('success', response.data)

        output = await communicator.receive_output()
        self.assertEqual(output['type'], 'websocket.close')

        await communicator.disconnect()

        cache_channel = cache.get(USER_CHANNEL_WS_LOGGED.format(user_id=self.user.id))
        self.assertIsNone(cache_channel)

    async def test_two_open_ws_tabs(self):
        communicator_1 = await self._connect_to_websocket()
        communicator_2 = await self._connect_to_websocket(test_connected_false=True)

        await communicator_1.disconnect()
        await communicator_2.disconnect()

