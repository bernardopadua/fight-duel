from django.db import transaction
from django.db.models import QuerySet

from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import NotFound, ValidationError

from mmo.models import Player, Item, PlayerInventory, Fight
from market.models import MarketDeal
from market.serializers import MarketDealSerializer

from typing import Any, override

LIMIT_DEAL_PER_PAGE = 20

class MarketDealCreateListView(ListCreateAPIView):

    serializer_class = MarketDealSerializer
    permission_classes = [IsAuthenticated]

    @override
    def get_queryset(self) -> QuerySet[MarketDeal]:
        min_power = self.request.query_params.get('minPower')
        max_power = self.request.query_params.get('maxPower')

        min_currency_amount = self.request.query_params.get('minCurrencyAmount')
        max_currency_amount = self.request.query_params.get('maxCurrencyAmount')

        order_by = self.request.query_params.get('orderBy', '')
        asc_desc = self.request.query_params.get('ascDesc', 'desc')
        
        def validate_value(value: Any) -> int:
            try:
                return int(value)
            except ValueError:
                raise ValidationError('Invalid parameters')
            except Exception:
                raise ValidationError('Something went wrong, contact support')

        page = validate_value(self.request.query_params.get('page', 1))

        queryset = MarketDeal.objects.select_related('item', 'player')

        if min_power:
            queryset = queryset.filter(item__item_power__gte=validate_value(min_power))
        if max_power:
            queryset = queryset.filter(item__item_power__lte=validate_value(max_power))
        
        if min_currency_amount:
            queryset = queryset.filter(
                market_currency_amount__gte=validate_value(min_currency_amount)
            )
        if max_currency_amount:
            queryset = queryset.filter(
                market_currency_amount__lte=validate_value(max_currency_amount)
            )

        field_orderby = 'market_created_date'
        if order_by == 'price':
            field_orderby = 'market_currency_amount'
        elif order_by == 'power':
            field_orderby = 'item__item_power'
        elif order_by == 'weight':
            field_orderby = 'item__item_weight'

        if asc_desc != 'asc':
            field_orderby = f'-{field_orderby}'

        queryset = queryset.order_by(field_orderby)

        return queryset[(page-1)*LIMIT_DEAL_PER_PAGE:page*LIMIT_DEAL_PER_PAGE]
    
    @override
    def perform_create(self, serializer: MarketDealSerializer) -> None:
        try:
            p = Player.objects.get(user=self.request.user)
        except Player.DoesNotExist:
            raise NotFound('Player not found')
        
        serializer.save(player=p)

class MarketDealRUDView(RetrieveUpdateDestroyAPIView):
    serializer_class = MarketDealSerializer
    permission_classes = [IsAuthenticated]

    @override
    def get_queryset(self) -> QuerySet[MarketDeal]:
        return MarketDeal.objects.filter(
            player__user=self.request.user
        ).select_related(
            'item', 'player'
        )

class MarketDealPurchaseView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request: Request, pk: int) -> Response:
        with transaction.atomic():
            if Fight.objects.filter(player__user=request.user).exists():
                raise ValidationError({'error': 'You cannot buy items while fighting'})
            
            buyer = Player.objects.select_for_update().filter(
                user=request.user
            ).first()        
            if not buyer:
                raise NotFound({'error': 'Buyer doesn\'t have a character'}) 

            market_deal = MarketDeal.objects.select_for_update().filter(
                id=pk
            ).select_related('item', 'player').first()
            if not market_deal:
                raise NotFound({'error': 'Deal not found'})

            if buyer.id == market_deal.player.id:
                raise ValidationError({'error': 'You cannot buy your own item'})

            if buyer.player_currency < market_deal.market_currency_amount:
                raise ValidationError({'error': 'Buyer doesn\'t have enough currency'})

            item_owner: Player = market_deal.player
            item: Item = market_deal.item

            item_owner_inventory = PlayerInventory.objects.select_for_update().filter(
                item=item,
                player=item_owner
            ).first()
            if not item_owner_inventory:
                raise NotFound({'error': 'Item not found in seller inventory'})

            # Transaction
            item_owner.player_currency += market_deal.market_currency_amount
            buyer.player_currency -= market_deal.market_currency_amount
            buyer.save(update_fields=['player_currency'])
            item_owner.save(update_fields=['player_currency'])
            item_owner_inventory.delete()
            PlayerInventory.objects.create(
                item=item,
                player=buyer
            )
            # End Transaction
            
            market_deal.delete()

            return Response(
                {
                    'success': True, 
                    'message': f'Successfully bought {item.item_name} from {item_owner.player_name}'
                },
                status=200
            )
