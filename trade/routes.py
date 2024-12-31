from django.urls import path
from . import butFx

urlpatterns = [
    path('buy/', butFx.fxBuy, name='fxBuy'),
]
