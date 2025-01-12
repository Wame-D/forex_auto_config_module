from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from forex.clickhouse.connection import get_clickhouse_client

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
def save_symbols(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            token = data.get('token')
            symbols = data.get('symbols')  # Expecting an array of symbols

            # Validate input
            if not token or not symbols:
                return JsonResponse({"error": "Token and symbols are required"}, status=400)
            if not isinstance(symbols, list):
                return JsonResponse({"error": "Symbols must be a list"}, status=400)

            # Prepare and execute bulk insertion
            for symbol in symbols:
                client.command(f"""
                    INSERT INTO symbols (token, symbol, created_at) 
                    VALUES ('{token}', '{symbol}', NOW())
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
                SELECT started_at, trading
                FROM userdetails 
                WHERE token = '{token}'
            """)
            
            if result:
                data = result.result_set[0]
                timestamp = data[0]
                trading = data[1]
                formatted_timestamp = timestamp.isoformat()
                return JsonResponse({"start_time": formatted_timestamp, 'trading':trading}, status=200)
            else:
                return JsonResponse({"error": "Token not found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

@csrf_exempt
def get_strategy(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            token = data.get('token')

            if not token:
                return JsonResponse({"error": "Token is required"}, status=400)

            # Fetch the strategy from the database
            result = client.query(f"""
                SELECT strategy
                FROM userdetails 
                WHERE token = '{token}'
            """)
            
            if result:
                data = result.result_set[0]
                strategy= data[0]
                return JsonResponse({"strategy": strategy}, status=200)
            else:
                return JsonResponse({"error": "Token not found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

@csrf_exempt
def get_symbol(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            token = data.get('token')

            if not token:
                return JsonResponse({"error": "Token is required"}, status=400)

            # Fetch the strategy from the database
            result = client.query(f"""
                SELECT symbol
                FROM symbols
                WHERE token = '{token}'
            """)
            if result:
                symbol = result.result_set
                # strategy= data[0]
                return JsonResponse({"symbol": symbol}, status=200)
            else:
                return JsonResponse({"error": "Token not found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)