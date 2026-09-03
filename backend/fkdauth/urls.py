from django.urls import path
from .views import (
    LoginView, RegisterUserView, 
    HealthCheck, LogoutView, 
    RefreshJWTView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterUserView.as_view(), name='register'),
    path('health-check/', HealthCheck.as_view(), name='health-check'),
    path('refresh-jwt/', RefreshJWTView.as_view(), name='refresh-jwt')
]
