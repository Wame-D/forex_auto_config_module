from .connection import get_clickhouse_client
from datetime import datetime, timedelta
import pytz  # Import pytz for timezone handling
import asyncio
import threading
from django.http import JsonResponse
from django.test import RequestFactory
from .views import get_risks


def eligible(email):
    # Simulate a POST request
    factory = RequestFactory()
    request = factory.post('/get_risks/', data={'email': email}, content_type='application/json')

    response = get_risks(request)

    # Print or process the response
    print(response.content)
