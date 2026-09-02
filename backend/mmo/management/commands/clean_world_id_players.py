from django.core.management.base import BaseCommand
from mmo.models import Player

class Command(BaseCommand):
    help = "Remove players stuck in worlds"

    def handle(self, *args, **kwargs):
        Player.objects.filter(
            player_world__isnull=False
        ).update(
            player_world=None
        )
