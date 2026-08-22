from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('fkdauth.urls'), name="auth"),
    path('api/mmo/', include('mmo.urls'), name="mmo")
]
