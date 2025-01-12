from django.contrib import admin
from django.urls import path
from authorise_deriv.views import authorize_user
from apache_superset.views import get_guest_token
from bot_settings.views import save_token_and_strategy
from bot_settings.views import update_trading_status
from bot_settings.views import get_start_time
from bot_settings.views import get_strategy
from django.urls import include, path
from analysis_module.view import forex_data_view,ForexAnalysisView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('authorize/', authorize_user, name='authorize_user'),
    path('generate-guest-token/', get_guest_token, name='generate_guest_token'),
    path('save-strategy/',save_token_and_strategy, name='save_token_and_strategy' ),
    path('update-trading/', update_trading_status, name='update_trading_status'),
    path('start-time/', get_start_time, name='get_start_time'),
    path('choosen-strategy/', get_strategy, name='get_strategy' ),
    path('trade/', include('trade.routes')),
    path('forex-data/', forex_data_view, name='forex_data'),    
    path('forex-analysis/', ForexAnalysisView.as_view(), name='forex-analysis'),

]
