from django.contrib import admin
from django.urls import path
from authorise_deriv.views import authorize_user
from apache_superset.views import get_guest_token
from django.urls import include, path

# bot setting urls
from bot_settings.views import save_token_and_strategy
from bot_settings.views import update_trading_status
from bot_settings.views import get_start_time
from bot_settings.views import get_strategy
from bot_settings.views import save_symbols
from bot_settings.views import get_symbol
from bot_settings.views import delete_symbol
from bot_settings.views import save_risks
from bot_settings.views import profit_and_loss_margin
from bot_settings.views import get_risks
from bot_settings.views import get_profit_and_loss_margin
from bot_settings.views import delete_candles
from forex.swagger import schema_view
from bot_settings.views import get_candles
from bot_settings.views import get_latest_candle

from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


urlpatterns = [
    #swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=2), name='schema-swagger-ui'),
    path('doc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'), 

    path('admin/', admin.site.urls),
    path('authorize/', authorize_user, name='authorize_user'),
    path('generate-guest-token/', get_guest_token, name='generate_guest_token'),
    # path('trade/', include('trade.routes')),   

    # bot setings
    path('save-strategy/',save_token_and_strategy, name='save_token_and_strategy' ),
    path('save_symbols/', save_symbols, name='save_symbols' ),
    path('update-trading/', update_trading_status, name='update_trading_status'),
    path('Get-start-time/', get_start_time, name='get_start_time'),
    path('choosen-strategy/', get_strategy, name='get_strategy' ),
    path('get_candles/', get_candles, name='get_candles' ),
    path('get_latest_candle/', get_latest_candle, name='get_latest_candle' ),
    path('get_symbols/', get_symbol, name='get_symbol' ),
    path('delete_symbols/', delete_symbol, name='delete_symbol' ),
    path('save_risks/', save_risks, name='save_risks' ),
    path('get_risks/', get_risks, name='get_risks' ),
    path('save_profit_and_loss/', profit_and_loss_margin, name='profit_and_loss_margin' ),
    path('get_profit_and_loss/', get_profit_and_loss_margin, name='get_profit_and_loss_margin' ),
    path('delete-candles/', delete_candles, name='delete_candles' ),

]
