from django.urls import path
from . import views

urlpatterns = [
    path('sendemail/', views.send_email_api, name='send_email_api'),
    
]
