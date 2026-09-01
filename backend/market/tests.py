from rest_framework.test import APITestCase
from rest_framework import status

from django.contrib.auth.models import User

from mmo.consumers import FightEngine, PlayerInventoryEngine
from mmo.models import Item, World, WorldCreature, Player
from market.models import MarketDeal
from mmo.services.fight_engine import FightStart
from mmo.services.world_engine import WorldEngine

class MarketTests(APITestCase):
    
    def setUp(self) -> None:
        #Copying this from MMO, since it has the same setup but with a little more stuff
        #still doesn't worth to creates a new TestCase for both.
        self.user = User.objects.create_user(username='test', email='test@test.com', password='123456')
        self.client.force_authenticate(user=self.user)
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
        self.item_power_armour = 50
        self.item_weight_armour = 50
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

        PlayerInventoryEngine.loot_items(
            self.player.id, [
                self.item_life_potion.id, 
                self.item_armour.id, 
                self.item_weapon.id
        ])

    def _create_item_in_market(self) -> int:
        response = self.client.post(
            '/api/market/',
            {
                'player': self.player.id,
                'item': self.item_life_potion.id,
                'marketCurrencyAmount': 1000
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.json().get('id'))
        self.assertEqual(response.json().get('item'), self.item_life_potion.id)
        self.assertEqual(response.json().get('marketCurrencyAmount'), 1000)
        self.assertEqual(response.json().get('itemPower'), self.item_life_potion.item_power)

        item_potion =MarketDeal.objects.filter(item=self.item_life_potion).first()
        self.assertIsNotNone(item_potion)

        return int(response.json().get('id'))

    def _create_item_expensive_in_market(self) -> int:
        response = self.client.post(
            '/api/market/',
            {
                'player': self.player.id,
                'item': self.item_armour.id,
                'marketCurrencyAmount': 9999999
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.json().get('id'))
        self.assertEqual(response.json().get('item'), self.item_armour.id)
        self.assertEqual(response.json().get('marketCurrencyAmount'), 9999999)

        item_armour = MarketDeal.objects.filter(item=self.item_armour).first()
        self.assertIsNotNone(item_armour)

        return int(response.json().get('id'))

    def _create_a_new_user_and_login(self):
        new_user = User.objects.create_user(username='new_user', email='newuser@new.com', password='654321')
        self.client.force_authenticate(user=new_user)

        self.new_player = Player.objects.create(
            player_name='NewUser',
            player_level=10,
            player_power=100,
            player_life=100,
            user=new_user,
            player_currency=1000
        )

    def test_market_create_and_listing_item(self):
        response = self.client.get(
            '/api/market/',
            {
                'orderBy': 'price',
                'ascDesc': 'desc'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        _ = self._create_item_in_market()

        item_potion_id = self.item_life_potion.id

        response = self.client.get(
            '/api/market/',
            {
                'orderBy': 'price',
                'ascDesc': 'desc'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        response = self.client.get(
            '/api/market/',
            {
                'orderBy': 'price',
                'ascDesc': 'desc',
                'page': 2
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        _ = self._create_item_expensive_in_market()

        item_expensive_id = self.item_armour.id

        response = self.client.get(
            '/api/market/',
            {
                'orderBy': 'price',
                'ascDesc': 'asc'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0].get('item'), item_potion_id)
        self.assertEqual(response.json()[1].get('item'), item_expensive_id)
        
        response = self.client.get(
            '/api/market/',
            {
                'orderBy': 'price',
                'ascDesc': 'desc'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0].get('item'), item_expensive_id)
        self.assertEqual(response.json()[1].get('item'), item_potion_id)

        response = self.client.get(
            '/api/market/',
            {
                'orderBy': 'power',
                'ascDesc': 'asc'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0].get('item'), item_potion_id)
        self.assertEqual(response.json()[1].get('item'), item_expensive_id)

        response = self.client.get(
            '/api/market/',
            {
                'orderBy': 'power',
                'ascDesc': 'desc'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0].get('item'), item_expensive_id)
        self.assertEqual(response.json()[1].get('item'), item_potion_id)

        response = self.client.get(
            '/api/market/',
            {
                'orderBy': 'weight',
                'ascDesc': 'asc'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0].get('item'), item_potion_id)
        self.assertEqual(response.json()[1].get('item'), item_expensive_id)

        response = self.client.get(
            '/api/market/',
            {
                'orderBy': 'weight',
                'ascDesc': 'desc'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0].get('item'), item_expensive_id)
        self.assertEqual(response.json()[1].get('item'), item_potion_id)


    def move_into_a_fight(self, player_id: int) -> FightStart:
        wr = WorldEngine.enter_world(player_id, self.world.id)
        self.assertIsNotNone(wr)
        self.assertEqual(wr.world_name, self.world.world_name) #pyright: ignore
        
        fs = FightEngine.should_fight(
            player_id
        )

        self.assertIsNotNone(fs)

        return fs #pyright: ignore (assert above)

    def test_market_item_purchase_successful(self):
        market_deal_id = self._create_item_in_market()
        self._create_a_new_user_and_login()

        market_deal = MarketDeal.objects.select_related(
            'player'
        ).filter(id=market_deal_id).first()

        self.assertIsNotNone(market_deal)
        self.assertEqual(market_deal.player.id, self.player.id)

        current_seller_amount = self.player.player_currency
        current_buyer_amount = self.new_player.player_currency

        response = self.client.post(f'/api/market/{market_deal_id}/buy/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.json())
        self.assertEqual(response.json()['success'], True)
        self.assertContains(response, self.item_life_potion.item_name)

        self.player.refresh_from_db()
        self.new_player.refresh_from_db()

        self.assertEqual(
            self.player.player_currency, 
            max(0, current_seller_amount + market_deal.market_currency_amount)
        )
        self.assertEqual(
            self.new_player.player_currency, 
            max(0, current_buyer_amount - market_deal.market_currency_amount)
        )


    def test_market_purchase_fail_same_player(self):
        market_deal_id = self._create_item_in_market()
        
        response = self.client.post(f'/api/market/{market_deal_id}/buy/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'You cannot buy your own item')
    
    def test_market_purchase_fail_not_enough_currency(self):
        market_deal_id = self._create_item_in_market()
        self._create_a_new_user_and_login()

        self.new_player.player_currency = 1
        self.new_player.save(update_fields=['player_currency'])

        response = self.client.post(f'/api/market/{market_deal_id}/buy/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'Buyer doesn\'t have enough currency')

    def test_market_purchase_inexistent_deal(self):
        response = self.client.post(f'/api/market/{0}/buy/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_market_cannot_buy_fighting_player(self):
        market_deal_id = self._create_item_in_market()
        self._create_a_new_user_and_login()

        _ = self.move_into_a_fight(self.new_player.id)

        response = self.client.post(f'/api/market/{market_deal_id}/buy/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'You cannot buy items while fighting')

