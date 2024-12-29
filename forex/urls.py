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
from authorise_deriv import views  # Corrected import

urlpatterns = [
    path('admin/', admin.site.urls),
    path('authorize/', views.authorize_user, name='authorize_user'),
]