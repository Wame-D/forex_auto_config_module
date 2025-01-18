from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from forex.clickhouse.connection import get_clickhouse_client

# Initialize ClickHouse client
client = get_clickhouse_client()

# Saving user token to the database and strategy
@csrf_exempt
def save_token_and_strategy(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            token = data.get('token')
            email = data.get('email')
            strategy = data.get('strategy')
            trading = data.get('trading')

            # Validate input
            if not token or not strategy or not email:
                return JsonResponse({"error": "Email, token, and strategy are required"}, status=400)

            # Check if the user exists in the database
            result = client.query(f"""
                SELECT token, COUNT(*)
                FROM userdetails
                WHERE email = '{email}'
                GROUP BY token
            """)
            row_data = result.result_set
            count = len(row_data)

            if count > 0:
                # Retrieve the current token
                stored_token = row_data[0][0]

                # Update only if the token is different or strategy has changed
                if stored_token != token:
                    client.command(f"""
                        ALTER TABLE userdetails UPDATE token = '{token}', strategy = '{strategy}'
                        WHERE email = '{email}'
                    """)

                    client.command(f"""
                        ALTER TABLE symbols UPDATE token = '{token}'
                        WHERE email = '{email}'
                    """)
                else:
                    # Update the strategy alone if the token hasn't changed
                    client.command(f"""
                        ALTER TABLE userdetails UPDATE strategy = '{strategy}'
                        WHERE email = '{email}'
                    """)
            else:
                # Insert new data if the user doesn't exist
                client.command(f"""
                    INSERT INTO userdetails (email, token, strategy, trading, created_at)
                    VALUES ('{email}', '{token}', '{strategy}', '{trading}', NOW())
                """)

            return JsonResponse({"message": "Data saved successfully"}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

# Saving symbols 
@csrf_exempt
def save_symbols(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            token = data.get('token')
            email = data.get('email')
            symbols = data.get('symbols')  # Expecting an array of symbols

            # Validate input
            if not email or not symbols:
                return JsonResponse({"error": "email and symbols are required"}, status=400)
            if not isinstance(symbols, list):
                return JsonResponse({"error": "Symbols must be a list"}, status=400)

            # Prepare and execute bulk insertion
            for symbol in symbols:
                client.command(f"""
                    INSERT INTO symbols (email, token, symbol, created_at) 
                    VALUES ('{email}', '{token}', '{symbol}', NOW())
                 """)

            return JsonResponse({"message": "Data saved successfully"}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

# Updating the trading status of the user
@csrf_exempt
def update_trading_status(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            email = data.get('email')
            trading = data.get('trading')

            # Validate input
            if not email or trading is None:
                return JsonResponse({"error": "Token, email and trading status are required"}, status=400)

            # Update the trading status in ClickHouse
            if trading:
                client.command(f"""
                ALTER TABLE userdetails UPDATE trading = {trading}, started_at = NOW()
                WHERE email = '{email}'
                """)
            else:
                client.command(f"""
                    ALTER TABLE userdetails UPDATE trading = {trading}
                    WHERE email = '{email}'
                """)

            return JsonResponse({"message": "Trading status updated successfully"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

# Getting the time the user allowed the bot to start trading
@csrf_exempt
def get_start_time(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            email = data.get('email')

            if not email:
                return JsonResponse({"error": "email is required"}, status=400)

            # Fetch the start_time from the database
            result = client.query(f"""
                SELECT started_at, trading
                FROM userdetails 
                WHERE email = '{email}'
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

# Getting the strategy that the user selected
@csrf_exempt
def get_strategy(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            email = data.get('email')

            if not email:
                return JsonResponse({"error": "email is required"}, status=400)

            # Fetch the strategy from the database
            result = client.query(f"""
                SELECT strategy
                FROM userdetails 
                WHERE email = '{email}'
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

# Getting symbols that the user selected
@csrf_exempt
def get_symbol(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            email = data.get('email')

            if not email:
                return JsonResponse({"error": "email is required"}, status=400)

            # Fetch the strategy from the database
            result = client.query(f"""
                SELECT symbol
                FROM symbols
                WHERE email = '{email}'
            """)
            if result:
                symbol = result.result_set
                return JsonResponse({"symbol": symbol}, status=200)
            else:
                return JsonResponse({"error": "Token not found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

# dELETING SYMBOLS FROM THE DATABASE from the database
@csrf_exempt
def delete_symbol(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            email = data.get('email')
            symbol = data.get('index')

            if not email:
                return JsonResponse({"error": "email is required"}, status=400)

            # dELETING SYMBOLS FROM THE DATABASE from the database
            result = client.query(f"""
                DELETE FROM symbols WHERE symbol = '{symbol}' AND email = '{email}'
            """)
            if result:
                symbol = result.result_set
                return JsonResponse({"symbol": symbol}, status=200)
            else:
                return JsonResponse({"error": "Token not found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)
