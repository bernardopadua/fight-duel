from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('fkdauth.urls')),
    path('api/mmo/', include('mmo.urls')),
    path('api/market/', include('market.urls'))
]
