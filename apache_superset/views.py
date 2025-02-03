import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

SUPERTSET_LOGIN_URL = "http://109.74.196.98:8088/api/v1/security/login" 

SUPERTSET_USERNAME = "admin"
SUPERTSET_PASSWORD = "forex123forex#"  

@csrf_exempt 
def get_guest_token(request):
    # Prepare login data
    login_data = {
        "username": SUPERTSET_USERNAME,
        "password": SUPERTSET_PASSWORD,
        "provider": "db", 
        "refresh": True,
    }

    # Make POST request to login to Superset and get the token
    response = requests.post(SUPERTSET_LOGIN_URL, json=login_data)

    if response.status_code == 200:
        # Parse the access token from the response
        access_token = response.json().get("access_token")
        print(access_token)
        encoded_jwt =  get_guest_token_for_dashboard(access_token)
        return JsonResponse({"guest_token": encoded_jwt})
    else:
        return JsonResponse({"error": "Failed to authenticate with Superset", "message": response.text})

def get_guest_token_for_dashboard(access_token):
    dashboard_id= "81429aff-ef7f-45a7-b31b-2eb06d86c1ce"
    dashboard_id1 = "fa733f1c-698c-47e8-9eeb-b4ab38f0adcf"
    url = "http://109.74.196.98:8088/api/v1/security/guest_token/"
    response = requests.post(
        url,
        data=json.dumps(
            {
                "user": {
                    "username": "guest",
                    "first_name": "daniel",
                    "last_name": "wame",
                },
                "resources": [
                    {
                        "type": "dashboard",
                        "id": dashboard_id,
                    },
                    {
                        "type": "dashboard",
                        "id": dashboard_id1,
                    }
                ],
                "rls": [],
            }
        ),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    )
    response_json = response.json()
  
    return response_json.get("token")