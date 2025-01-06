from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# from clickhouse_connect import Client
import json
from forex.clickhouse.connection import get_clickhouse_client
import pandas as pd

# Initialize ClickHouse client
client = get_clickhouse_client()

@csrf_exempt
def save_token_and_strategy(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            token = data.get('token')
            strategy = data.get('strategy')
            trading = data.get('trading')

            # Validate input
            if not token or not strategy:
                return JsonResponse({"error": "Token and strategy are required"}, status=400)

            # Save data to ClickHouse
            client.command(f"""
                INSERT INTO userdetails (token, strategy, trading, created_at) 
                VALUES ('{token}', '{strategy}', '{trading}', NOW())
            """)

            return JsonResponse({"message": "Data saved successfully"}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)


@csrf_exempt
def update_trading_status(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            token = data.get('token')
            trading = data.get('trading')

            # Validate input
            if not token or trading is None:
                return JsonResponse({"error": "Token and trading status are required"}, status=400)

            # Update the trading status in ClickHouse
            if trading:
                client.command(f"""
                ALTER TABLE userdetails UPDATE trading = {trading}, started_at = NOW()
                WHERE token = '{token}'
                """)
            else:
                client.command(f"""
                    ALTER TABLE userdetails UPDATE trading = {trading}
                    WHERE token = '{token}'
                """)

            return JsonResponse({"message": "Trading status updated successfully"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)


@csrf_exempt
def get_start_time(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            token = data.get('token')

            if not token:
                return JsonResponse({"error": "Token is required"}, status=400)

            # Fetch the start_time from the database
            result = client.query(f"""
                SELECT started_at
                FROM userdetails 
                WHERE token = '{token}'
            """)
            
            if result:
                data = result.result_set[0]
                timestamp = data[0]
                formatted_timestamp = timestamp.isoformat()
                return JsonResponse({"start_time": formatted_timestamp}, status=200)
            else:
                return JsonResponse({"error": "Token not found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)