from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command

from mmo.models import Fight, Player, World, WorldCreature
from mmo.services.fight_engine import FightEngine
from mmo.services.world_engine import WorldEngine

class TestCommands(TestCase):
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
    
    def test_clean_locked_fights(self):
        wr = WorldEngine.enter_world(self.player.id, self.world.id)
        self.assertIsNotNone(wr)
        self.assertEqual(self.world.world_name, wr.world_name) #pyright: ignore
        fs = FightEngine.should_fight(self.player.id)
        self.assertIsNotNone(fs)
        self.assertEqual(Fight.objects.count(), 1)

        call_command("clean_locked_fights")

        self.player.refresh_from_db()
        self.assertEqual(Fight.objects.count(), 0)
        self.assertEqual(self.player.player_status, Player.PlayerStatus.IDLE)
