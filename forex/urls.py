from django.contrib import admin
from django.urls import path
from authorise_deriv.views import authorize_user
from apache_superset.views import get_guest_token
from bot_settings.views import save_token_and_strategy
from bot_settings.views import update_trading_status
from bot_settings.views import get_start_time
from bot_settings.views import get_strategy
from bot_settings.views import save_symbols
from bot_settings.views import get_symbol
from django.urls import include, path
from bot_settings.views import delete_symbol
from analysis_module.view import forex_analysis

urlpatterns = [
    path('admin/', admin.site.urls),
    path('authorize/', authorize_user, name='authorize_user'),
    path('generate-guest-token/', get_guest_token, name='generate_guest_token'),
    path('save-strategy/',save_token_and_strategy, name='save_token_and_strategy' ),
    path('update-trading/', update_trading_status, name='update_trading_status'),
    path('start-time/', get_start_time, name='get_start_time'),
    path('choosen-strategy/', get_strategy, name='get_strategy' ),
    path('save_symbols/', save_symbols, name='save_symbols' ),
    path('get_symbols/', get_symbol, name='get_symbol' ),
    path('delete_symbols/', delete_symbol, name='delete_symbol' ),
    path('trade/', include('trade.routes')),    
    #path('api/get_candles/', get_candles, name='get_candles'),
    path('api/forex-analysis/', forex_analysis, name='forex_analysis'),  # Add the route for the analysis


]
