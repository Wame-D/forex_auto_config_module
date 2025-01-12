# from django.contrib import admin
# from django.urls import path, re_path, include
# from rest_framework.permissions import AllowAny
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi
# from authorise_deriv.views import authorize_user
# # from authorise_deriv.views import get_forex_data

# # Swagger schema configuration
# schema_view = get_schema_view(
#     openapi.Info(
#         title="Forex API",
#         default_version="v1",
#         description="API documentation for the Forex project",
#         terms_of_service="https://www.google.com/policies/terms/",
#         contact=openapi.Contact(email="support@forexproject.com"),
#         license=openapi.License(name="BSD License"),
#     ),
#     public=True,
#     permission_classes=(AllowAny,),
# )

# # URL patterns
# urlpatterns = [
#     path("admin/", admin.site.urls),  # Admin panel
#     path("authorize/", authorize_user, name="authorize_user"),  # Authorize endpoint
#       # Include URLs from the forex app
#     # path("api/", include("forex.urls")),
#     # path("forex_data/", get_forex_data, name="get_forex_data"),  # Forex data endpoint

#     # Swagger UI endpoints
#     re_path(
#         r"^swagger(?P<format>\.json|\.yaml)$",
#         schema_view.without_ui(cache_timeout=0),
#         name="schema-json",
#     ),
#     path(
#         "swagger/",
#         schema_view.with_ui("swagger", cache_timeout=0),
#         name="schema-swagger-ui",
#     ),
#     path(
#         "redoc/",
#         schema_view.with_ui("redoc", cache_timeout=0),
#         name="schema-redoc",
#     ),
# ]

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
]
