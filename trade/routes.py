from django.urls import path
from . import views

urlpatterns = [
    path('buy/', views.main, name='main'),
]
