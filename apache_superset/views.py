from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
import os
import jwt

# Load environment variables from .env file
load_dotenv()

PRIVATE_KEY = os.getenv('PRIVATE_KEY_CONTENT')
key_id = "3dfea0d265190fe0"  # Key ID from the Preset UI

def get_guest_token(request):
    """
    Generates a guest token to be used by the Preset SDK.
    """

    # Payload to encode
    payload = {
        "user": { 
            "username": "Daniel Wame",
            "first_name": "Daniel",
            "last_name": "Wame"
        },
        "resources": [  # Specify the dashboard(s) the user should have access to
            {"type": "dashboard", "id": "afe0ee9c-4bda-4694-8877-eca384df8ffb"}
        ],
        "rls_rules": [  # RLS rules that should be applied
            {"dataset": 16, "clause": "environment = 'production'"},
            {"dataset": 42, "clause": "state = 'published'"}
        ],
        "type": "guest",
        "aud": "970dc793",  # The Workspace ID
    }

    # Encode the JWT
    encoded_jwt = jwt.encode(
        payload,
        PRIVATE_KEY,
        algorithm="RS256",
        headers={"kid": key_id}
    )

    # Return the token as a JSON response
    return JsonResponse({"guest_token": encoded_jwt})
