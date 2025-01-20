from django.shortcuts import render
from django.http import JsonResponse
from deriv_api import DerivAPI
from django.views.decorators.csrf import csrf_exempt
import json
# Initialize DerivAPI client
app_id = 65102
@csrf_exempt
async def authorize_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
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

async def balance(token):
    try:
        # Initialize the API
        api = DerivAPI(app_id=app_id)
        authorize = await api.authorize(token)
        
        if not authorize:
            raise ValueError("Authorization failed")

        # Get account balance
        response = await api.balance()
        account_balance = response.get('balance', {}).get('balance', 0)

        return account_balance
    except Exception as e:
        return 0


