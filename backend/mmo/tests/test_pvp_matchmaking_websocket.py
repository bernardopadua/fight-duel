from asgiref.sync import sync_to_async

from unittest.mock import patch

from django.test import TransactionTestCase, override_settings
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User

from channels.testing import WebsocketCommunicator

from core.asgi import application

from mmo.consumers import ToServerActions, ToClientActions
from mmo.models import Player, World, WorldCreature, Item, Fight
from mmo.constants import USER_CHANNEL_WS_LOGGED
from mmo.tasks.task_matchmaking import clean_up_matchmaking_fight

from fkdauth.jwt_auth_utils import create_token

@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}},
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "game-consumer-tests"
        }
    }
)
class MMOPVPMatchmakingConsumerTests(TransactionTestCase):
    """
        Testing matchmaking and pvp fight websocket consumer.
        Like the test in test_api_websocket.py this test 
        takes in consideration the client side thats why some messages are silent.
    """
    def setUp(self) -> None:
        cache.clear()

        self.user = User.objects.create_user(username='test', email='test@test.com', password='123456')
        self.user_2 = User.objects.create_user(username='test_2', email='test_2@test.com', password='123456')

        self.token = create_token(self.user.id, settings.SECRET_KEY)
        self.token_2 = create_token(self.user_2.id, settings.SECRET_KEY)

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

        self.player_life = 100
        self.player_power = 10
        self.player = Player.objects.create(
            player_name='TestPlayer',
            player_level=10,
            player_power=10,
            player_life=self.player_life,
            user=self.user,
            player_world=self.world
        )

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

    async def _connect_to_websocket_p1(self) -> WebsocketCommunicator:
        token_headers = [
            (b'cookie', f'Authorization-JWT={self.token}'.encode()),
        ]
        communicator = WebsocketCommunicator(
            application, '/ws/fight/',
            headers=token_headers
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        return communicator

    async def _connect_to_websocket_p2(self) -> WebsocketCommunicator:
        token_headers = [
            (b'cookie', f'Authorization-JWT={self.token_2}'.encode()),
        ]
        communicator = WebsocketCommunicator(
            application, '/ws/fight/',
            headers=token_headers
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        return communicator

    @patch('mmo.consumers.MatchmakingEngine.matchmaking_cleanup_task_run')
    async def test_matchmaking_found_match_1_vs_1(self, mock_matchmaking_cleanup_task_run):
        com1 = await self._connect_to_websocket_p1()
        com2 = await self._connect_to_websocket_p2()

        with patch('mmo.services.fight_engine.random.randint', return_value=1): #1 is the percent to fit 10 percent of chance
            await com1.send_json_to({'action': ToServerActions.MOVE})
            response_1 = await com1.receive_json_from()

            mock_matchmaking_cleanup_task_run.assert_called_once()

            self.assertIn('action', response_1)
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_START)

            response_2 = await com2.receive_json_from()

            self.assertIn('action', response_2)
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING)
            self.assertIn('data', response_2)
            self.assertIn('fightId', response_2['data'])
            self.assertEqual(response_2['data']['fightId'], response_1['data']['fightId'])
            self.assertIn('challengerName', response_2['data'])
            self.assertIn('challengerLevel', response_2['data'])
            self.assertEqual(response_2['data']['challengerName'], self.player.player_name)
            self.assertEqual(response_2['data']['challengerLevel'], self.player.player_level)
        
        await com1.disconnect()
        await com2.disconnect()
    
    @patch('mmo.consumers.MatchmakingEngine.matchmaking_cleanup_task_run')
    async def test_matchmaking_found_match_1_vs_1_reject_mm(self, mock_matchmaking_cleanup_task_run):
        com1 = await self._connect_to_websocket_p1()
        com2 = await self._connect_to_websocket_p2()
       
        with patch('mmo.services.fight_engine.random.randint', return_value=1): #1 is the percent to fit 10 percent of chance
            await com1.send_json_to({'action': ToServerActions.MOVE})
            response_1 = await com1.receive_json_from()

            mock_matchmaking_cleanup_task_run.assert_called_once()

            self.assertIn('action', response_1)
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_START)
            self.assertIn('fightId', response_1['data'])

            current_fight = response_1['data']['fightId']
            self.assertIsInstance(current_fight, int)

            response_2 = await com2.receive_json_from()

            self.assertIn('action', response_2)
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING)
            self.assertIn('data', response_2)
            self.assertIn('fightId', response_2['data'])
            self.assertEqual(response_2['data']['fightId'], response_1['data']['fightId'])
            self.assertIn('challengerName', response_2['data'])
            self.assertIn('challengerLevel', response_2['data'])
            self.assertEqual(response_2['data']['challengerName'], self.player.player_name)
            self.assertEqual(response_2['data']['challengerLevel'], self.player.player_level)
    
        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNotNone(f)

        await com2.send_json_to({'action': ToServerActions.REJECT_MATCHMAKING})
        
        response_1 = await com1.receive_json_from()
        response_2 = await com2.receive_json_from()

        self.assertIn('data', response_1)
        self.assertIn('action', response_1)
        self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_REJECT)
        self.assertIn('fightId', response_1['data'])
        self.assertEqual(response_1['data']['fightId'], current_fight)

        self.assertIn('data', response_2)
        self.assertIn('action', response_2)
        self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING_REJECT)
        self.assertIn('fightId', response_1['data'])
        self.assertEqual(response_2['data']['fightId'], current_fight)

        await com1.disconnect()
        await com2.disconnect()

    @patch('mmo.consumers.monster_attack.apply_async')
    @patch('mmo.consumers.MatchmakingEngine.matchmaking_cleanup_task_run')
    async def test_user_in_world_but_not_connected(self, mock_matchmaking_cleanup_task_run, mock_monster_attack_apply_sync):
        com1 = await self._connect_to_websocket_p1()
        com2 = await self._connect_to_websocket_p2()
        
        cache.delete(USER_CHANNEL_WS_LOGGED.format(user_id=self.player_2.user.id))

        with patch('mmo.services.fight_engine.random.randint', return_value=1): #1 is the percent to fit 10 percent of chance
            await com1.send_json_to({'action': ToServerActions.MOVE})
            response_1 = await com1.receive_json_from()
            
            mock_matchmaking_cleanup_task_run.assert_not_called()
            mock_monster_attack_apply_sync.assert_called_once()

            self.assertIn('action', response_1)
            self.assertEqual(response_1['action'], ToClientActions.FIGHT)
        
        await com1.disconnect()
        await com2.disconnect()

    @patch('mmo.consumers.MatchmakingEngine.matchmaking_cleanup_task_run')
    async def test_matchmaking_found_match_1_vs_1_accept_mm(self, mock_matchmaking_cleanup_task_run):
        com1 = await self._connect_to_websocket_p1()
        com2 = await self._connect_to_websocket_p2()
       
        with patch('mmo.services.fight_engine.random.randint', return_value=1): #1 is the percent to fit 10 percent of chance
            await com1.send_json_to({'action': ToServerActions.MOVE})
            response_1 = await com1.receive_json_from()

            mock_matchmaking_cleanup_task_run.assert_called_once()

            self.assertIn('action', response_1)
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_START)
            self.assertIn('fightId', response_1['data'])

            current_fight = response_1['data']['fightId']
            self.assertIsInstance(current_fight, int)

            response_2 = await com2.receive_json_from()

            self.assertIn('action', response_2)
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING)
            self.assertIn('data', response_2)
            self.assertIn('fightId', response_2['data'])
            self.assertEqual(response_2['data']['fightId'], response_1['data']['fightId'])
            self.assertIn('challengerName', response_2['data'])
            self.assertIn('challengerLevel', response_2['data'])
            self.assertEqual(response_2['data']['challengerName'], self.player.player_name)
            self.assertEqual(response_2['data']['challengerLevel'], self.player.player_level)
    
        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNotNone(f)

        await com2.send_json_to({'action': ToServerActions.ACCEPT_MATCHMAKING})

        response_1 = await com1.receive_json_from()
        response_2 = await com2.receive_json_from()

        self.assertIn('action', response_1)
        self.assertEqual(response_1['action'], ToClientActions.FIGHT)
        self.assertIn('data', response_1)
        self.assertIn('fightId', response_1['data'])
        self.assertEqual(response_1['data']['fightId'], current_fight)
        self.assertIn('opponents', response_1['data'])
        self.assertEqual(len(response_1['data']['opponents']), 2)
        
        self.assertIn('action', response_2)
        self.assertEqual(response_2['action'], ToClientActions.FIGHT)
        self.assertIn('data', response_2)
        self.assertIn('fightId', response_2['data'])
        self.assertEqual(response_2['data']['fightId'], current_fight)
        self.assertIn('opponents', response_2['data'])
        self.assertEqual(len(response_2['data']['opponents']), 2)

        await com1.disconnect()
        await com2.disconnect()

    @patch('mmo.consumers.MatchmakingEngine.matchmaking_cleanup_task_run')
    async def test_matchmaking_found_match_1_vs_1_accept_mm_same_user(self, mock_matchmaking_cleanup_task_run):
        com1 = await self._connect_to_websocket_p1()
        com2 = await self._connect_to_websocket_p2()
       
        with patch('mmo.services.fight_engine.random.randint', return_value=1): #1 is the percent to fit 10 percent of chance
            await com1.send_json_to({'action': ToServerActions.MOVE})
            response_1 = await com1.receive_json_from()

            mock_matchmaking_cleanup_task_run.assert_called_once()

            self.assertIn('action', response_1)
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_START)
            self.assertIn('fightId', response_1['data'])

            current_fight = response_1['data']['fightId']
            self.assertIsInstance(current_fight, int)

            response_2 = await com2.receive_json_from()

            self.assertIn('action', response_2)
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING)
            self.assertIn('data', response_2)
            self.assertIn('fightId', response_2['data'])
            self.assertEqual(response_2['data']['fightId'], response_1['data']['fightId'])
            self.assertIn('challengerName', response_2['data'])
            self.assertIn('challengerLevel', response_2['data'])
            self.assertEqual(response_2['data']['challengerName'], self.player.player_name)
            self.assertEqual(response_2['data']['challengerLevel'], self.player.player_level)
    
        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNotNone(f)

        #COM1 created and tries do accept the matchmaking
        await com1.send_json_to({'action': ToServerActions.ACCEPT_MATCHMAKING})

        self.assertTrue(await com1.receive_nothing())
        self.assertTrue(await com2.receive_nothing())

        await com1.disconnect()
        await com2.disconnect()

    @patch('mmo.consumers.MatchmakingEngine.matchmaking_cleanup_task_run')
    async def test_matchmaking_found_match_1_vs_1_attack_pvp(self, mock_matchmaking_cleanup_task_run):
        com1 = await self._connect_to_websocket_p1()
        com2 = await self._connect_to_websocket_p2()
       
        with patch('mmo.services.fight_engine.random.randint', return_value=1): #1 is the percent to fit 10 percent of chance
            await com1.send_json_to({'action': ToServerActions.MOVE})
            response_1 = await com1.receive_json_from()

            mock_matchmaking_cleanup_task_run.assert_called_once()

            self.assertIn('action', response_1)
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_START)
            self.assertIn('fightId', response_1['data'])

            current_fight = response_1['data']['fightId']
            self.assertIsInstance(current_fight, int)

            response_2 = await com2.receive_json_from()

            self.assertIn('action', response_2)
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING)
            self.assertIn('data', response_2)
            self.assertIn('fightId', response_2['data'])
            self.assertEqual(response_2['data']['fightId'], response_1['data']['fightId'])
            self.assertIn('challengerName', response_2['data'])
            self.assertIn('challengerLevel', response_2['data'])
            self.assertEqual(response_2['data']['challengerName'], self.player.player_name)
            self.assertEqual(response_2['data']['challengerLevel'], self.player.player_level)
    
        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNotNone(f)

        await com2.send_json_to({'action': ToServerActions.ACCEPT_MATCHMAKING})

        response_1 = await com1.receive_json_from()
        response_2 = await com2.receive_json_from()

        self.assertIn('action', response_1)
        self.assertEqual(response_1['action'], ToClientActions.FIGHT)
        self.assertIn('data', response_1)
        self.assertIn('fightId', response_1['data'])
        self.assertEqual(response_1['data']['fightId'], current_fight)
        self.assertIn('opponents', response_1['data'])
        self.assertEqual(len(response_1['data']['opponents']), 2)
        
        self.assertIn('action', response_2)
        self.assertEqual(response_2['action'], ToClientActions.FIGHT)
        self.assertIn('data', response_2)
        self.assertIn('fightId', response_2['data'])
        self.assertEqual(response_2['data']['fightId'], current_fight)
        self.assertIn('opponents', response_2['data'])
        self.assertEqual(len(response_2['data']['opponents']), 2)

        await com1.send_json_to({'action': ToServerActions.ATTACK})
        response_1 = await com1.receive_json_from()
        response_2 = await com2.receive_json_from()

        self.assertIn('action', response_1)
        self.assertEqual(response_1['action'], ToClientActions.FIGHT_UPDATE)
        self.assertIn('data', response_1)
        self.assertIn('isPlayerAlive', response_1['data'])
        self.assertIn('isOpponentAlive', response_1['data'])
        self.assertIn('playerLife', response_1['data'])
        self.assertIn('opponentLife', response_1['data'])
        self.assertIn('isFightOver', response_1['data'])
        self.assertEqual(response_1['data']['isPlayerAlive'], True)
        self.assertEqual(response_1['data']['isOpponentAlive'], True)
        self.assertEqual(response_1['data']['isFightOver'], False)
        self.assertEqual(response_1['data']['playerLife'], self.player.player_max_life)
        self.assertEqual(response_1['data']['playerName'], self.player.player_name)
        self.assertEqual(response_1['data']['opponentName'], self.player_2.player_name)

        self.assertIn('action', response_2)
        self.assertEqual(response_2['action'], ToClientActions.FIGHT_UPDATE)
        self.assertIn('data', response_2)
        self.assertIn('isPlayerAlive', response_2['data'])
        self.assertIn('isOpponentAlive', response_2['data'])
        self.assertIn('playerLife', response_2['data'])
        self.assertIn('opponentLife', response_2['data'])
        self.assertIn('isFightOver', response_2['data'])
        self.assertEqual(response_2['data']['isPlayerAlive'], True)
        self.assertEqual(response_2['data']['isOpponentAlive'], True)
        self.assertEqual(response_2['data']['isFightOver'], False)
        self.assertLess(response_2['data']['playerLife'], self.player_2.player_max_life)
        self.assertEqual(response_2['data']['playerName'], self.player_2.player_name)
        self.assertEqual(response_2['data']['opponentName'], self.player.player_name)

        await com1.disconnect()
        await com2.disconnect()        

    @patch('mmo.consumers.MatchmakingEngine.matchmaking_cleanup_task_run')
    async def test_matchmaking_found_match_1_vs_1_attack_pvp_spam_second_ignored(self, mock_matchmaking_cleanup_task_run):
        com1 = await self._connect_to_websocket_p1()
        com2 = await self._connect_to_websocket_p2()
       
        with patch('mmo.services.fight_engine.random.randint', return_value=1): #1 is the percent to fit 10 percent of chance
            await com1.send_json_to({'action': ToServerActions.MOVE})
            response_1 = await com1.receive_json_from()

            mock_matchmaking_cleanup_task_run.assert_called_once()

            self.assertIn('action', response_1)
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_START)
            self.assertIn('fightId', response_1['data'])

            current_fight = response_1['data']['fightId']
            self.assertIsInstance(current_fight, int)

            response_2 = await com2.receive_json_from()

            self.assertIn('action', response_2)
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING)
            self.assertIn('data', response_2)
            self.assertIn('fightId', response_2['data'])
            self.assertEqual(response_2['data']['fightId'], response_1['data']['fightId'])
            self.assertIn('challengerName', response_2['data'])
            self.assertIn('challengerLevel', response_2['data'])
            self.assertEqual(response_2['data']['challengerName'], self.player.player_name)
            self.assertEqual(response_2['data']['challengerLevel'], self.player.player_level)
    
        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNotNone(f)

        await com2.send_json_to({'action': ToServerActions.ACCEPT_MATCHMAKING})

        response_1 = await com1.receive_json_from()
        response_2 = await com2.receive_json_from()

        self.assertIn('action', response_1)
        self.assertEqual(response_1['action'], ToClientActions.FIGHT)
        self.assertIn('data', response_1)
        self.assertIn('fightId', response_1['data'])
        self.assertEqual(response_1['data']['fightId'], current_fight)
        self.assertIn('opponents', response_1['data'])
        self.assertEqual(len(response_1['data']['opponents']), 2)
        
        self.assertIn('action', response_2)
        self.assertEqual(response_2['action'], ToClientActions.FIGHT)
        self.assertIn('data', response_2)
        self.assertIn('fightId', response_2['data'])
        self.assertEqual(response_2['data']['fightId'], current_fight)
        self.assertIn('opponents', response_2['data'])
        self.assertEqual(len(response_2['data']['opponents']), 2)

        await com1.send_json_to({'action': ToServerActions.ATTACK})
        response_1 = await com1.receive_json_from()
        response_2 = await com2.receive_json_from()
        self.assertIn('action', response_1)
        self.assertEqual(response_1['action'], ToClientActions.FIGHT_UPDATE)
        self.assertIn('action', response_2)
        self.assertEqual(response_2['action'], ToClientActions.FIGHT_UPDATE)

        await com1.send_json_to({'action': ToServerActions.ATTACK})
        self.assertTrue(await com1.receive_nothing())
        self.assertTrue(await com2.receive_nothing())
    
        await com1.disconnect()
        await com2.disconnect()

    @patch('mmo.consumers.MatchmakingEngine.matchmaking_cleanup_task_run')
    async def test_matchmaking_found_match_1_vs_1_attack_pvp_no_stamina(self, mock_matchmaking_cleanup_task_run):
        self.player.player_stamina = 1
        self.player.player_power = 10
        await self.player.asave(update_fields=['player_stamina', 'player_power'])

        com1 = await self._connect_to_websocket_p1()
        com2 = await self._connect_to_websocket_p2()
       
        with patch('mmo.services.fight_engine.random.randint', return_value=1): #1 is the percent to fit 10 percent of chance
            await com1.send_json_to({'action': ToServerActions.MOVE})
            response_1 = await com1.receive_json_from()

            mock_matchmaking_cleanup_task_run.assert_called_once()

            self.assertIn('action', response_1)
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_START)
            self.assertIn('fightId', response_1['data'])

            current_fight = response_1['data']['fightId']
            self.assertIsInstance(current_fight, int)

            response_2 = await com2.receive_json_from()

            self.assertIn('action', response_2)
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING)
            self.assertIn('data', response_2)
            self.assertIn('fightId', response_2['data'])
            self.assertEqual(response_2['data']['fightId'], response_1['data']['fightId'])
            self.assertIn('challengerName', response_2['data'])
            self.assertIn('challengerLevel', response_2['data'])
            self.assertEqual(response_2['data']['challengerName'], self.player.player_name)
            self.assertEqual(response_2['data']['challengerLevel'], self.player.player_level)
    
        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNotNone(f)

        await com2.send_json_to({'action': ToServerActions.ACCEPT_MATCHMAKING})

        response_1 = await com1.receive_json_from()
        response_2 = await com2.receive_json_from()

        self.assertIn('action', response_1)
        self.assertEqual(response_1['action'], ToClientActions.FIGHT)
        self.assertIn('data', response_1)
        self.assertIn('fightId', response_1['data'])
        self.assertEqual(response_1['data']['fightId'], current_fight)
        self.assertIn('opponents', response_1['data'])
        self.assertEqual(len(response_1['data']['opponents']), 2)
        
        self.assertIn('action', response_2)
        self.assertEqual(response_2['action'], ToClientActions.FIGHT)
        self.assertIn('data', response_2)
        self.assertIn('fightId', response_2['data'])
        self.assertEqual(response_2['data']['fightId'], current_fight)
        self.assertIn('opponents', response_2['data'])
        self.assertEqual(len(response_2['data']['opponents']), 2)

        await com1.send_json_to({'action': ToServerActions.ATTACK})
        self.assertTrue(await com1.receive_nothing())
        self.assertTrue(await com2.receive_nothing())
    
        await com1.disconnect()
        await com2.disconnect()

    @patch('mmo.consumers.MatchmakingEngine.matchmaking_cleanup_task_run')
    async def test_matchmaking_found_match_1_vs_1_attack_player_two_died_no_drop(self, mock_matchmaking_cleanup_task_run):
        self.player.player_power = 9999
        await self.player.asave(update_fields=['player_power'])

        com1 = await self._connect_to_websocket_p1()
        com2 = await self._connect_to_websocket_p2()
       
        with patch('mmo.services.fight_engine.random.randint', return_value=1): #1 is the percent to fit 10 percent of chance
            await com1.send_json_to({'action': ToServerActions.MOVE})
            response_1 = await com1.receive_json_from()

            mock_matchmaking_cleanup_task_run.assert_called_once()

            self.assertIn('action', response_1)
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_START)
            self.assertIn('fightId', response_1['data'])

            current_fight = response_1['data']['fightId']
            self.assertIsInstance(current_fight, int)

            response_2 = await com2.receive_json_from()

            self.assertIn('action', response_2)
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING)
    
        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNotNone(f)

        await com2.send_json_to({'action': ToServerActions.ACCEPT_MATCHMAKING})

        response_1 = await com1.receive_json_from()
        response_2 = await com2.receive_json_from()

        self.assertIn('action', response_1)
        self.assertEqual(response_1['action'], ToClientActions.FIGHT)
        
        self.assertIn('action', response_2)
        self.assertEqual(response_2['action'], ToClientActions.FIGHT)

        with patch('mmo.services.drop_engine.DropEngine.calculate_chance_drop_by_player', return_value=0):
            await com1.send_json_to({'action': ToServerActions.ATTACK})
            response_1 = await com1.receive_json_from()
            response_2 = await com2.receive_json_from()
            self.assertIn('action', response_1)
            self.assertIn('data', response_1)
            self.assertIn('isFightOver', response_1['data'])
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_FINISH)
            self.assertEqual(response_1['data']['playerLife'], self.player.player_max_life)
            self.assertEqual(response_1['data']['opponentLife'], 0)
            self.assertEqual(response_1['data']['isFightOver'], True)

            self.assertIn('action', response_2)
            self.assertIn('data', response_2)
            self.assertIn('isFightOver', response_2['data'])
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_FINISH)
            self.assertEqual(response_2['data']['playerLife'], 0)
            self.assertEqual(response_2['data']['opponentLife'], self.player.player_max_life)
            self.assertEqual(response_2['data']['isFightOver'], True)

        await com1.disconnect()
        await com2.disconnect()

    @patch('mmo.consumers.MatchmakingEngine.matchmaking_cleanup_task_run')
    async def test_matchmaking_found_match_1_vs_1_attack_player_two_died_with_drop(self, mock_matchmaking_cleanup_task_run):
        self.player.player_power = 9999
        await self.player.asave(update_fields=['player_power'])

        com1 = await self._connect_to_websocket_p1()
        com2 = await self._connect_to_websocket_p2()
       
        with patch('mmo.services.fight_engine.random.randint', return_value=1): #1 is the percent to fit 10 percent of chance
            await com1.send_json_to({'action': ToServerActions.MOVE})
            response_1 = await com1.receive_json_from()

            mock_matchmaking_cleanup_task_run.assert_called_once()

            self.assertIn('action', response_1)
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_START)
            self.assertIn('fightId', response_1['data'])

            current_fight = response_1['data']['fightId']
            self.assertIsInstance(current_fight, int)

            response_2 = await com2.receive_json_from()

            self.assertIn('action', response_2)
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING)
    
        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNotNone(f)

        await com2.send_json_to({'action': ToServerActions.ACCEPT_MATCHMAKING})

        response_1 = await com1.receive_json_from()
        response_2 = await com2.receive_json_from()

        self.assertIn('action', response_1)
        self.assertEqual(response_1['action'], ToClientActions.FIGHT)
        
        self.assertIn('action', response_2)
        self.assertEqual(response_2['action'], ToClientActions.FIGHT)

        with (
            patch('mmo.services.drop_engine.DropEngine.calculate_chance_drop_by_player', return_value=100),
            patch('mmo.services.drop_engine.DropEngine.calculate_chance_drop_currency', return_value=100)
        ):
            await com1.send_json_to({'action': ToServerActions.ATTACK})
            response_1 = await com1.receive_json_from()
            response_2 = await com2.receive_json_from()

            self.assertIn('action', response_1)
            self.assertIn('data', response_1)
            self.assertIsInstance(response_1['data'], list)
            self.assertGreater(len(response_1['data']), 0)
            self.assertIn('itemName', response_1['data'][0])
            self.assertIn('itemPower', response_1['data'][0])

            response_1 = await com1.receive_json_from()
            await self.player.arefresh_from_db()

            self.assertIn('action', response_1)
            self.assertIn('data', response_1)
            self.assertIn('isFightOver', response_1['data'])
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_FINISH)
            self.assertEqual(response_1['data']['playerLife'], self.player.player_max_life)
            self.assertEqual(response_1['data']['opponentLife'], 0)
            self.assertEqual(response_1['data']['isFightOver'], True)
            self.assertGreater(self.player.player_exp, 0)
            self.assertGreater(self.player.player_currency, 0)

            self.assertIn('action', response_2)
            self.assertIn('data', response_2)
            self.assertIn('isFightOver', response_2['data'])
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_FINISH)
            self.assertEqual(response_2['data']['playerLife'], 0)
            self.assertEqual(response_2['data']['opponentLife'], self.player.player_max_life)
            self.assertEqual(response_2['data']['isFightOver'], True)

        await com1.disconnect()
        await com2.disconnect()

    @patch('mmo.consumers.MatchmakingEngine.matchmaking_cleanup_task_run')
    async def test_matchmaking_found_match_1_vs_1_flee(self, mock_matchmaking_cleanup_task_run):
        self.player.player_power = 9999
        await self.player.asave(update_fields=['player_power'])

        com1 = await self._connect_to_websocket_p1()
        com2 = await self._connect_to_websocket_p2()
       
        with patch('mmo.services.fight_engine.random.randint', return_value=1): #1 is the percent to fit 10 percent of chance
            await com1.send_json_to({'action': ToServerActions.MOVE})
            response_1 = await com1.receive_json_from()

            mock_matchmaking_cleanup_task_run.assert_called_once()

            self.assertIn('action', response_1)
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_START)
            self.assertIn('fightId', response_1['data'])

            current_fight = response_1['data']['fightId']
            self.assertIsInstance(current_fight, int)

            response_2 = await com2.receive_json_from()

            self.assertIn('action', response_2)
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING)
    
        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNotNone(f)

        await com2.send_json_to({'action': ToServerActions.ACCEPT_MATCHMAKING})

        response_1 = await com1.receive_json_from()
        response_2 = await com2.receive_json_from()

        self.assertIn('action', response_1)
        self.assertEqual(response_1['action'], ToClientActions.FIGHT)
        
        self.assertIn('action', response_2)
        self.assertEqual(response_2['action'], ToClientActions.FIGHT)

        await com2.send_json_to({'action': ToServerActions.FLEE})
        response_1 = await com1.receive_json_from()
        response_2 = await com2.receive_json_from()
        
        self.assertIn('action', response_1)
        self.assertEqual(response_1['action'], ToClientActions.FIGHT_FINISH)
        self.assertIn('data', response_1)
        self.assertIn('isFightOver', response_1['data'])
        self.assertTrue(response_1['data']['isFightOver'])
        self.assertEqual(response_1['data']['playerName'], self.player.player_name)
        self.assertEqual(response_1['data']['opponentName'], self.player_2.player_name)

        self.assertIn('action', response_2)
        self.assertEqual(response_2['action'], ToClientActions.FIGHT_FINISH)
        self.assertIn('data', response_2)
        self.assertIn('isFightOver', response_2['data'])
        self.assertTrue(response_2['data']['isFightOver'])
        self.assertEqual(response_2['data']['playerName'], self.player_2.player_name)
        self.assertEqual(response_2['data']['opponentName'], self.player.player_name)
        
        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNone(f)

        await com1.disconnect()
        await com2.disconnect()

    @patch('mmo.consumers.MatchmakingEngine.matchmaking_cleanup_task_run')
    async def test_matchmaking_found_match_1_vs_1_player_two_disconnect(self, mock_matchmaking_cleanup_task_run):
        self.player.player_power = 9999
        await self.player.asave(update_fields=['player_power'])

        com1 = await self._connect_to_websocket_p1()
        com2 = await self._connect_to_websocket_p2()
       
        with patch('mmo.services.fight_engine.random.randint', return_value=1): #1 is the percent to fit 10 percent of chance
            await com1.send_json_to({'action': ToServerActions.MOVE})
            response_1 = await com1.receive_json_from()

            mock_matchmaking_cleanup_task_run.assert_called_once()

            self.assertIn('action', response_1)
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_START)
            self.assertIn('fightId', response_1['data'])

            current_fight = response_1['data']['fightId']
            self.assertIsInstance(current_fight, int)

            response_2 = await com2.receive_json_from()

            self.assertIn('action', response_2)
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING)
    
        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNotNone(f)

        await com2.send_json_to({'action': ToServerActions.ACCEPT_MATCHMAKING})

        response_1 = await com1.receive_json_from()
        response_2 = await com2.receive_json_from()

        self.assertIn('action', response_1)
        self.assertEqual(response_1['action'], ToClientActions.FIGHT)
        
        self.assertIn('action', response_2)
        self.assertEqual(response_2['action'], ToClientActions.FIGHT)    

        await com2.disconnect()

        response_1 = await com1.receive_json_from()

        self.assertIn('action', response_1)
        self.assertEqual(response_1['action'], ToClientActions.FIGHT_FINISH)
        self.assertIn('data', response_1)
        self.assertIn('isFightOver', response_1['data'])
        self.assertTrue(response_1['data']['isFightOver'])

    @patch('mmo.consumers.MatchmakingEngine.matchmaking_cleanup_task_run')
    async def test_matchmaking_found_match_1_vs_1_cleanup_fight(self, mock_matchmaking_cleanup_task_run):
        self.player.player_power = 9999
        await self.player.asave(update_fields=['player_power'])

        com1 = await self._connect_to_websocket_p1()
        com2 = await self._connect_to_websocket_p2()
       
        with patch('mmo.services.fight_engine.random.randint', return_value=1): #1 is the percent to fit 10 percent of chance
            await com1.send_json_to({'action': ToServerActions.MOVE})
            response_1 = await com1.receive_json_from()

            mock_matchmaking_cleanup_task_run.assert_called_once()

            self.assertIn('action', response_1)
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_START)
            self.assertIn('fightId', response_1['data'])

            current_fight = response_1['data']['fightId']
            self.assertIsInstance(current_fight, int)

            response_2 = await com2.receive_json_from()

            self.assertIn('action', response_2)
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING)
    
        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNotNone(f)

        await sync_to_async(clean_up_matchmaking_fight)(f.id)

        response_1 = await com1.receive_json_from()
        response_2 = await com2.receive_json_from()
        
        self.assertIn('action', response_1)
        self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_TIMEOUT)
        self.assertIn('data', response_1)
        self.assertIn('fightId', response_1['data'])
        self.assertEqual(response_1['data']['fightId'], current_fight)

        self.assertIn('action', response_2)
        self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING_TIMEOUT)
        self.assertIn('data', response_2)
        self.assertIn('fightId', response_2['data'])
        self.assertEqual(response_2['data']['fightId'], current_fight)

        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNone(f)

        await self.player.arefresh_from_db()
        await self.player_2.arefresh_from_db()

        self.assertEqual(self.player.player_status, Player.PlayerStatus.IDLE)
        self.assertEqual(self.player_2.player_status, Player.PlayerStatus.IDLE)

        await com1.disconnect()
        await com2.disconnect()

    @patch('mmo.consumers.MatchmakingEngine.matchmaking_cleanup_task_run')
    async def test_matchmaking_found_match_1_vs_1_disconnecting_before_accept(self, mock_matchmaking_cleanup_task_run):
        com1 = await self._connect_to_websocket_p1()
        com2 = await self._connect_to_websocket_p2()
       
        with patch('mmo.services.fight_engine.random.randint', return_value=1): #1 is the percent to fit 10 percent of chance
            await com1.send_json_to({'action': ToServerActions.MOVE})
            response_1 = await com1.receive_json_from()

            mock_matchmaking_cleanup_task_run.assert_called_once()

            self.assertIn('action', response_1)
            self.assertEqual(response_1['action'], ToClientActions.FIGHT_MATCHMAKING_START)
            self.assertIn('fightId', response_1['data'])

            current_fight = response_1['data']['fightId']
            self.assertIsInstance(current_fight, int)

            response_2 = await com2.receive_json_from()

            self.assertIn('action', response_2)
            self.assertEqual(response_2['action'], ToClientActions.FIGHT_MATCHMAKING)
            self.assertIn('data', response_2)
            self.assertIn('fightId', response_2['data'])
            self.assertEqual(response_2['data']['fightId'], response_1['data']['fightId'])
            self.assertIn('challengerName', response_2['data'])
            self.assertIn('challengerLevel', response_2['data'])
            self.assertEqual(response_2['data']['challengerName'], self.player.player_name)
            self.assertEqual(response_2['data']['challengerLevel'], self.player.player_level)
    
        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNotNone(f)

        await com1.disconnect()

        response_2 = await com2.receive_json_from()
        self.assertIn('action', response_2)
        self.assertEqual(response_2['action'], ToClientActions.FIGHT_FINISH)
        self.assertIn('data', response_2)
        self.assertIn('isFightOver', response_2['data'])
        self.assertTrue(response_2['data']['isFightOver'])

        f = await Fight.objects.filter(
            id=current_fight,
            player=self.player,
            opponent=self.player_2
        ).afirst()
        self.assertIsNone(f)

        await self.player.arefresh_from_db()
        await self.player_2.arefresh_from_db()

        self.assertEqual(self.player.player_status, Player.PlayerStatus.IDLE)
        self.assertEqual(self.player_2.player_status, Player.PlayerStatus.IDLE)

        await com2.disconnect()

