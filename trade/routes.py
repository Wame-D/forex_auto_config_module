from django.urls import path
from . import views

urlpatterns = [
    path('multiplier/', views.fxTradeMultiplier, name='fxTradeMultiplier'),
    path('sell/', views.fxCloseMultiplierTrade, name='fxCloseMultiplierTrade'),
]
