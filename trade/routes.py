from django.urls import path
from . import views

urlpatterns = [
    path('multiplier/', views.executeTrade, name='executeTrade'),
    path('sell/', views.fxCloseMultiplierTrade, name='fxCloseMultiplierTrade'),
]
