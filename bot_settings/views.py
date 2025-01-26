from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from forex.clickhouse.connection import get_clickhouse_client
from datetime import datetime, date 

# Initialize ClickHouse client
client = get_clickhouse_client()
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from authorise_deriv.views import balance
from rest_framework import serializers

# Define your parameters for documentation
token_param = openapi.Parameter('token', openapi.IN_BODY, description="Authentication token", type=openapi.TYPE_STRING)
email_param = openapi.Parameter('email', openapi.IN_BODY, description="User's email", type=openapi.TYPE_STRING)
strategy_param = openapi.Parameter('strategy', openapi.IN_BODY, description="Trading strategy", type=openapi.TYPE_STRING)
trading_param = openapi.Parameter('trading', openapi.IN_BODY, description="Trading details", type=openapi.TYPE_BOOLEAN)

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

# @swagger_auto_schema(
#     method='POST', 
#     request_body=openapi.Schema(
#         type=openapi.TYPE_OBJECT,
#         properties={
#             'token': openapi.Schema(type=openapi.TYPE_STRING),
#             'email': openapi.Schema(type=openapi.TYPE_STRING),
#             'strategy': openapi.Schema(type=openapi.TYPE_STRING),  # strategy as a string
#             'trading': openapi.Schema(type=openapi.TYPE_STRING)
#         }
#     )
# )
# @api_view(['POST'])
# Saving user token to the database and strategy
@csrf_exempt
async def save_token_and_strategy(request):
    client = get_clickhouse_client()
    # name = request.query_params.get('name', None)
    if request.method == 'POST':
        try:

            client.command("""
                CREATE TABLE IF NOT EXISTS userdetails (
                    email String,
                    token String,
                    strategy String,
                    trading String,
                    trading_today String,
                    balance Float32,
                    balance_today Float32, 
                    created_at DateTime,
                    started_at DateTime
                ) ENGINE = MergeTree()
                ORDER BY (email);
            """)
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
                account_balance = await balance(token)
                # Insert new data if the user doesn't exist
                client.command(f"""
                    INSERT INTO userdetails (email, token, strategy, trading, balance,balance_today, created_at)
                    VALUES ('{email}', '{token}', '{strategy}', '{trading}',{account_balance},{account_balance}, NOW())
                """)

            return JsonResponse({"message": "Data saved successfully"}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

# Updating the trading status of the user
@swagger_auto_schema(method='PUT', 
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'trading': openapi.Schema(type=openapi.TYPE_BOOLEAN)
        }
    )
)
@api_view(['PUT'])
@csrf_exempt
def update_trading_status(request):
    if request.method == 'PUT':
        try:
            client = get_clickhouse_client()
            # Parse JSON data from the request
            data = json.loads(request.body)
            email = data.get('email')
            trading = data.get('trading')

            # Validate input
            if not email or trading is None:
                return JsonResponse({"error": "Token, email and trading status are required"}, status=400)

            # Update the trading status in ClickHouse
            if trading:
                """
                Checks if the start_date for the given email is today.

                Args:
                    client: The database client object.
                    email: The email address to check.

                Returns:
                    True if the start_date is today, False otherwise
                    then if start date is today, start trading immediately or wait for that day.
                """
                result = client.query(f"""
                SELECT start_date
                FROM start_stop_table
                WHERE email = '{email}'
                """)

                if result.result_set:
                    start_date_str = result.result_set[0][0]
                    start_date = start_date_str.date()
                    today = date.today()

                    if start_date == today:
                        client.command(f"""
                        ALTER TABLE userdetails UPDATE trading = {trading}, started_at = NOW()
                        WHERE email = '{email}'
                        """)
                    else:
                        return JsonResponse({
                            "message": "Trading status updated successfully.",
                            "start_date": start_date.strftime('%Y-%m-%d')
                        }, status=200)
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
@swagger_auto_schema(
    method='GET',
    query_serializer=EmailSerializer,  # Use query_serializer for GET requests
    responses={200: openapi.Response('Success')}
)
@api_view(['GET'])
@csrf_exempt
def get_start_time(request):
    if request.method == 'GET':
        try:
            client = get_clickhouse_client()
            # Access query parameters
            email = request.query_params.get('email')

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
@swagger_auto_schema(
    method='GET',
    query_serializer=EmailSerializer,  # Use query_serializer for GET requests
    responses={200: openapi.Response('Success')}
)
@api_view(['GET'])
@csrf_exempt
def get_strategy(request):
    if request.method == 'GET':
        try:
            client = get_clickhouse_client()
            # Parse JSON data from the request
            email = request.query_params.get('email')

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

""" 
user symols settings
saving saving symbols 

deleting symbols and 
getting user symbols

"""
# Saving symbols 
@swagger_auto_schema(method='post', 
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'token': openapi.Schema(type=openapi.TYPE_STRING),
            'symbol': openapi.Schema(type=openapi.TYPE_STRING),
        }
    )
)
@api_view(['POST'])
@csrf_exempt
def save_symbols(request):
    if request.method == 'POST':
        try:
            client = get_clickhouse_client()
            client.command("""
                CREATE TABLE IF NOT EXISTS symbols (
                    email String,
                    token String,
                    symbol String,
                    created_at DateTime
                ) ENGINE = MergeTree()
                ORDER BY (email);
            """)
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
                print(symbol, email, token)
                client.command(f"""
                    INSERT INTO symbols (email, token, symbol, created_at) 
                    VALUES ('{email}', '{token}', '{symbol}', NOW())
                """)

            return JsonResponse({"message": "Data saved successfully"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

# Getting symbols that the user selected
@swagger_auto_schema(
    method='GET',
    query_serializer=EmailSerializer,  # Use query_serializer for GET requests
    responses={200: openapi.Response('Success')}
)
@api_view(['GET'])
@csrf_exempt
def get_symbol(request):
    if request.method == 'GET':
        try:
            client = get_clickhouse_client()
            # Parse JSON data from the request
            email = request.query_params.get('email')

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
@swagger_auto_schema(method='DELETE', 
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'symbol': openapi.Schema(type=openapi.TYPE_STRING),
        }
    )
)
@api_view(['DELETE'])
@csrf_exempt
def delete_symbol(request):
    if request.method == 'DELETE':
        try:
            client = get_clickhouse_client()
            # Parse JSON data from the request
            data = json.loads(request.body)
            email = data.get('email')
            symbol = data.get('index')

            if not email:
                return JsonResponse({"error": "email is required"}, status=400)

            # dELETING SYMBOLS FROM THE DATABASE from the database
            result = client.query(f"""
                ALTER TABLE symbols DELETE WHERE symbol = '{symbol}' AND email = '{email}'
            """)
            if result:
                symbol = result.result_set
                return JsonResponse({"symbol": symbol}, status=200)
            else:
                return JsonResponse({"error": "Token not found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

# delete candles from database
@swagger_auto_schema(method='DELETE', 
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'symbol': openapi.Schema(type=openapi.TYPE_STRING),
        }
    )
)
@api_view(['DELETE'])
@csrf_exempt
def delete_candles(request):
    if request.method == 'DELETE':
        try:
            client = get_clickhouse_client()
            # Parse JSON data from the request
            data = json.loads(request.body)
            symbol = data.get('symbol')

            symbol_table_map = {
            "EUR/USD": "eurousd",
            "Gold/USD": "gold_candles",
            "V75": "v75_candles",
            "US30": "us30_candles"
            }
            table_name = symbol_table_map.get(symbol)

            if not symbol:
                return JsonResponse({"error": "symbol is required"}, status=400)

            # dELETING candles FROM THE DATABASE
            result = client.query(f"""
                TRUNCATE TABLE {table_name};
            """)
            if result:
                response = result.result_set
                return JsonResponse({" Data deleted successfully, response ": response}, status=200)
            else:
                return JsonResponse({"error": "symbol not found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

""" 
    Risk analysis setting setthings

    per trade risk and per day risk
    
"""
@swagger_auto_schema(method='post', 
    operation_id='Save risk percentage', 
    description="### Save Risk Percentage\nThis endpoint is used to save the risk percentage settings for trading strategies." ,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'per_trade ': openapi.Schema(type=openapi.TYPE_NUMBER),
            'per_day ': openapi.Schema(type=openapi.TYPE_NUMBER),
        }
    )
)
@api_view(['POST'])
@csrf_exempt
def save_risks(request):
    if request.method == 'POST':
        try:
            client = get_clickhouse_client()
            # Ensure the table exists
            client.command("""
                CREATE TABLE IF NOT EXISTS risk_table (
                    email String,
                    per_trade Float32,
                    per_day Float32,
                    created_at DateTime
                ) ENGINE = MergeTree()
                ORDER BY (email);
            """)

            # Parse JSON data from the request
            data = json.loads(request.body)
            day = data.get('per_day')
            email = data.get('email')
            trade = data.get('per_trade')

            # Validate input
            if not email or day is None:
                return JsonResponse({"error": "Email, day, and trade risks are required"}, status=400)
            
            if trade is None:
                trade = 1
                # setting default risk per trade to 1

            # Fetch existing risks for the user
            result = client.query(
                "SELECT per_trade, per_day FROM risk_table WHERE email = %(email)s",
                {"email": email}
            )
            row_data = result.result_set
            exists = len(row_data) > 0

            changes = {}

            if exists:
                # Extract the current risks
                existing_trade, existing_day = row_data[0]

                # Compare and update if necessary
                if float(existing_trade) != float(trade):
                    changes["per_trade"] = {"old": existing_trade, "new": trade}
                    client.command(
                        "ALTER TABLE risk_table UPDATE per_trade = %(trade)s WHERE email = %(email)s",
                        {"trade": trade, "email": email}
                    )

                if float(existing_day) != float(day):
                    changes["per_day"] = {"old": existing_day, "new": day}
                    client.command(
                        "ALTER TABLE risk_table UPDATE per_day = %(day)s WHERE email = %(email)s",
                        {"day": day, "email": email}
                    )
            else:
                # Insert new risks for the user if they don't exist
                client.command(
                    """
                    INSERT INTO risk_table (email, per_trade, per_day, created_at)
                    VALUES (%(email)s, %(trade)s, %(day)s, NOW())
                    """,
                    {"email": email, "trade": trade, "day": day}
                )
                changes["new_entry"] = {"per_trade": trade, "per_day": day}

            if changes:
                # Notify the user about what has changed
                return JsonResponse({"message": "Risks updated successfully", "changes": changes}, status=200)

            return JsonResponse({"message": "No changes were made, risks are already up to date"}, status=200)

        except Exception as e:
            # Handle server errors
            return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

# getting risk data from database
@swagger_auto_schema(
    method='GET',
    query_serializer=EmailSerializer,  # Use query_serializer for GET requests
    responses={200: openapi.Response('Success')}
)
@api_view(['GET'])
@csrf_exempt
def get_risks(request):
    if request.method == 'GET':
        try:
            client = get_clickhouse_client()
            # Access query parameters
            email = request.query_params.get('email')

            if not email:
                return JsonResponse({"error": "email is required"}, status=400)

            # Fetch the strategy from the database
            result = client.query(f"""
                SELECT per_trade, per_day
                FROM risk_table
                WHERE email = '{email}'
            """)
            if result:
                risks = result.result_set[0]
                return JsonResponse({"risks": risks}, status=200)
            else:
                return JsonResponse({"error": "email not found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

"""
    profit and loss marging 

    saving time frame when the bot shall stop executing 
    maximun loss per day
    and overall

    maximum win per day and overall
"""
# Define parameters for swagger documentation
email_param = openapi.Parameter('email', openapi.IN_BODY, description="User's email", type=openapi.TYPE_STRING)
max_loss_per_day_param = openapi.Parameter('max_loss_per_day', openapi.IN_BODY, description="Maximum loss per day", type=openapi.TYPE_NUMBER)
overall_loss_param = openapi.Parameter('overall_loss', openapi.IN_BODY, description="Overall loss", type=openapi.TYPE_NUMBER)
max_win_per_day_param = openapi.Parameter('max_win_per_day', openapi.IN_BODY, description="Maximum win per day", type=openapi.TYPE_NUMBER)
overall_win_param = openapi.Parameter('overall_win', openapi.IN_BODY, description="Overall win", type=openapi.TYPE_NUMBER)
start_date_param = openapi.Parameter('start_date', openapi.IN_BODY, description="Start date of the trading", type=openapi.TYPE_STRING)
stop_date_param = openapi.Parameter('stop_date', openapi.IN_BODY, description="Stop date of the trading", type=openapi.TYPE_STRING)

@swagger_auto_schema(method='post', 
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'max_loss_per_day': openapi.Schema(type=openapi.TYPE_NUMBER),
            'overall_loss': openapi.Schema(type=openapi.TYPE_NUMBER),
            'max_win_per_day': openapi.Schema(type=openapi.TYPE_NUMBER),
            'overall_win': openapi.Schema(type=openapi.TYPE_NUMBER),
            'start_date': openapi.Schema(type=openapi.TYPE_STRING),
            'stop_date': openapi.Schema(type=openapi.TYPE_STRING)
        }
    )
)
@api_view(['POST'])
@csrf_exempt
def profit_and_loss_margin(request):
    if request.method == 'POST':
        try:
            client = get_clickhouse_client()
            # Ensure the table exists
            client.command("""
                CREATE TABLE IF NOT EXISTS start_stop_table (
                    email String,
                    start_date DateTime,
                    stop_date DateTime,
                    loss_per_day Float32,
                    overall_loss Float32,
                    win_per_day Float32,
                    overall_win Float32,
                    created_at DateTime
                ) ENGINE = MergeTree()
                ORDER BY (email);
            """)


            #Parse JSON data from the request
            data = json.loads(request.body)

            email = data.get('email')
            loss_per_day = data.get('max_loss_per_day')
            overall_loss = data.get('overall_loss')
            win_per_day = data.get('max_win_per_day')
            overall_win = data.get('overall_win')
            start_date = data.get('start_date')
            stop_date = data.get('stop_date')

            # Validate input
            if not email or not  stop_date or loss_per_day is None or overall_loss is None or win_per_day is None or overall_win is None:
                return JsonResponse({
                    "error": "Email, start_date, loss_per_day, overall_loss, win_per_day, and overall_win are required"
                }, status=400)

            # Fetch existing details for the user
            result = client.query(f"""
            SELECT start_date, stop_date, loss_per_day, overall_loss, win_per_day, overall_win
            FROM start_stop_table
            WHERE email = '{email}'
            """)
            print(result.result_set)
            changes = {}

            if result :
                if result.result_set:
                    row_data = result.result_set[0]

                    # Extract the current settings
                    existing_start_date = row_data[0]
                    existing_stop_date = row_data[1]
                    existing_loss_per_day = row_data[2]
                    existing_overall_loss = row_data[3] 
                    existing_win_per_day = row_data[4]
                    existing_overall_win = row_data[5]

                    # Compare and update if necessary
                    if existing_start_date != start_date:
                        changes["start_date"] = {"old": str(existing_start_date), "new": str(start_date)}
                        client.command(
                            "ALTER TABLE start_stop_table UPDATE start_date = %(start_date)s WHERE email = %(email)s",
                            {"start_date": start_date, "email": email}
                        )

                    if existing_stop_date != stop_date:
                        changes["stop_date"] = {"old": str(existing_stop_date), "new": str(stop_date)}
                        client.command(
                            "ALTER TABLE start_stop_table UPDATE stop_date = %(stop_date)s WHERE email = %(email)s",
                            {"stop_date": stop_date, "email": email}
                        )


                    if float(existing_loss_per_day) != float(loss_per_day):
                        changes["loss_per_day"] = {"old": existing_loss_per_day, "new": loss_per_day}
                        client.command(
                            "ALTER TABLE start_stop_table UPDATE loss_per_day = %(loss_per_day)s WHERE email = %(email)s",
                            {"loss_per_day": loss_per_day, "email": email}
                        )

                    if float(existing_overall_loss) != float(overall_loss):
                        changes["overall_loss"] = {"old": existing_overall_loss, "new": overall_loss}
                        client.command(
                            "ALTER TABLE start_stop_table UPDATE overall_loss = %(overall_loss)s WHERE email = %(email)s",
                            {"overall_loss": overall_loss, "email": email}
                        )

                    if float(existing_win_per_day) != float(win_per_day):
                        changes["win_per_day"] = {"old": existing_win_per_day, "new": win_per_day}
                        client.command(
                            "ALTER TABLE start_stop_table UPDATE win_per_day = %(win_per_day)s WHERE email = %(email)s",
                            {"win_per_day": win_per_day, "email": email}
                        )

                    if float(existing_overall_win) != float(overall_win):
                        changes["overall_win"] = {"old": existing_overall_win, "new": overall_win}
                        client.command(
                            "ALTER TABLE start_stop_table UPDATE overall_win = %(overall_win)s WHERE email = %(email)s",
                            {"overall_win": overall_win, "email": email}
                        )
                else:
                    # Insert new details for the user if they don't exist
                    client.query(f"""
                        INSERT INTO start_stop_table (email, start_date, stop_date, loss_per_day, overall_loss, win_per_day, overall_win, created_at)
                        VALUES ('{email}', '{start_date}', '{stop_date}', '{loss_per_day}', '{overall_loss}', '{win_per_day}', '{overall_win}', NOW())
                        """
                    )
                    changes["new_entry"] = {
                        "start_date": str(start_date),
                        "loss_per_day": loss_per_day,
                        "overall_loss": overall_loss,
                        "win_per_day": win_per_day,
                        "overall_win": overall_win
                    }

                if changes:
                    # Notify the user about what has changed
                    return JsonResponse({"message": "Profit and loss margins updated successfully", "changes": changes}, status=200)

                return JsonResponse({"message": "No changes were made, settings are already up to date"}, status=200)
            else:
                return JsonResponse({"message": "No changes were made"}, status=300)
        except Exception as e:
            # Handle server errors
            return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

# getting profit and loss data data from database
@csrf_exempt
@swagger_auto_schema(
    method='GET',
    query_serializer=EmailSerializer,  # Use query_serializer for GET requests
    responses={200: openapi.Response('Success')}
)
@api_view(['GET'])
def get_profit_and_loss_margin(request):
    if request.method == 'GET':
        try:
            client = get_clickhouse_client()
            email = request.query_params.get('email')

            if not email:
                return JsonResponse({"error": "email is required"}, status=400)

            result = client.query(f"""
                SELECT start_date, stop_date, loss_per_day, overall_loss, win_per_day, overall_win
                FROM start_stop_table
                WHERE email = '{email}'
            """)
            
            if result :
                data = result.result_set[0]
                return JsonResponse({"data": data}, status=200)
            else:
                return JsonResponse({"error": "email not found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)