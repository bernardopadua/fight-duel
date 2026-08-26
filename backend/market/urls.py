from django.urls import path
from market.views import MarketDealCreateListView, MarketDealRUDView, MarketDealPurchaseView

urlpatterns = [
    path('', MarketDealCreateListView.as_view(), name='market-deals-list-create'),
    path('<int:pk>/', MarketDealRUDView.as_view(), name='market-deals-rud'),
    path('<int:pk>/buy/', MarketDealPurchaseView.as_view(), name='market-deals-buy')
]
