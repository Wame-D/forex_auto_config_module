from django.contrib import admin
from django.urls import path
from authorise_deriv.views import authorize_user
from apache_superset.views import get_guest_token
from analysis.views import perform_analysis

urlpatterns = [
    path('admin/', admin.site.urls),
    path('authorize/', authorize_user, name='authorize_user'),
    path('generate-guest-token/', get_guest_token, name='generate_guest_token'),
    path('perform-analysis/', perform_analysis, name='perform_analysis'),
]
