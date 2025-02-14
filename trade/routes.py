from django.urls import path
from . import views

urlpatterns = [
    path('multiplier/', views.executeTrade, name='executeTrade'),
    path('testapp',views.testApp, name='testApp'),
    path('getpt', views.getpt, name='getpt'),
    path('monitor', views.test_monitor_trades, name='test_monitor_trades'),
    path('testcontract', views.testContract, name='testContract')
]
