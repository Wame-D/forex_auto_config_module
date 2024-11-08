from django.shortcuts import render

# myapp/views.py
from django.http import JsonResponse
from deriv_api import DerivAPI
from django.views.decorators.csrf import csrf_exempt
import json

# Initialize DerivAPI client
app_id = 65102

@csrf_exempt
def authorize_user(request):
    if request.method == "POST":
        try:
            # data = json.loads(request.body)
            data = json.loads(request.body.decode('utf-8'))
            token = data.get("token")
            if not token:
                return JsonResponse({"error": "Token is required"}, status=400)

            api = DerivAPI(app_id=app_id)
            authorize = await api.authorize(token)

            if "error" in authorize:
                return JsonResponse({"error": authorize["error"]["message"]}, status=401)

            return JsonResponse({"authorize": authorize}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)
