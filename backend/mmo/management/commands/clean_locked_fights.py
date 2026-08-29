from django.core.management.base import BaseCommand
from mmo.models import Fight, Player

class Command(BaseCommand):
    help = "Clean up fights locked in DB before server starts"

    def handle(self, *args, **kwargs):
        Player.objects.filter(
            player_status=Player.PlayerStatus.FIGHTING
        ).update(
            player_status=Player.PlayerStatus.IDLE
        )
        Fight.objects.all().delete()
