from django.db import models

from mmo.models import Player, Item

class MarketDeal(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    market_currency_amount = models.IntegerField(default=0)
    market_created_date = models.DateTimeField(auto_now_add=True)

