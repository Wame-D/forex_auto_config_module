from django.urls import path
from . import views

urlpatterns =[
    path('ticks/', views.get_ticks)
]