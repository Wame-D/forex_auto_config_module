from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import json
from deriv_api import DerivAPI
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from authorise_deriv.models import ForexData 
# Initialize DerivAPI client
app_id = 65102

# Define input parameters for Swagger
token_param = openapi.Parameter('token', openapi.IN_BODY, description="The token for user authorization", type=openapi.TYPE_STRING)

@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Authorize user with a token",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'token': openapi.Schema(type=openapi.TYPE_STRING, description="User's token for authorization")
        }
    ),
    responses={
        200: openapi.Response("Authorization Successful", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
            'authorize': openapi.Schema(type=openapi.TYPE_OBJECT, description="Authorized user data")
        })),
        400: "Bad request - Missing token",
        401: "Unauthorized - Invalid token",
        500: "Server error"
    }
)
@api_view(['POST'])
async def authorize_user(request):
    if request.method == "POST":
        try:
            # Parse request data
            data = json.loads(request.body)
            token = data.get("token")

            if not token:
                return JsonResponse({"error": "Token is required"}, status=400)

            # Authorize using DerivAPI
            api = DerivAPI(app_id=app_id)
            authorize = await api.authorize(token)

            if "error" in authorize:
                return JsonResponse({"error": authorize["error"]["message"]}, status=401)

            return JsonResponse({"authorize": authorize}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
@api_view(['GET'])
def get_forex_data(request):
    """
    Get forex data from the database.
    Returns a list of forex data in JSON format.
    """
    try:
        forex_data = ForexData.objects.all().values()  # Fetch data from the database
        return JsonResponse(list(forex_data), safe=False, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
