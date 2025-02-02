import asyncio
from django.http import JsonResponse
from django.http import HttpResponse
from datetime import datetime, timedelta
from django.http import JsonResponse
import asyncio
from trade.contractManagement import fetch_contract_updates
from trade.tradeHistory import fetch_profit_table
import websockets
import json
from websocket import create_connection
from deriv_api import DerivAPI

from .buyAndSell import fxTradeMultiplier, fxCloseMultiplierTrade
from django.views.decorators.csrf import csrf_exempt


# -----------------------------------------
# Testing FUNCTION
def executeTrade(token, lot_size, tp, sl, symbol):
    # Define the proposal details
    proposal_details = {
        "url": "wss://ws.binaryws.com/websockets/v3?app_id=65102",
        "token": token, 
        "symbol": symbol,
        "amount": lot_size,  
        "multiplier": 100, 
        "take_profit": tp, 
        "stop_loss": sl  
    }

    # Call the fxTradeMultiplier function with the proposal details
    response = fxTradeMultiplier(
        url=proposal_details["url"],
        token=proposal_details["token"],
        symbol=proposal_details["symbol"],
        amount=proposal_details["amount"],
        multiplier=proposal_details["multiplier"],
        take_profit=proposal_details["take_profit"],
        stop_loss=proposal_details["stop_loss"]
    )
    
    # Print or handle the response
    print(response)
    return JsonResponse(response)

# -----------------------------------------
# test function for getting contract details
def testApp(request):
    # Replace these with your test token and parameters
    test_token = "a1-Rpkn31phHKJihM7NtL3HoMNiOb9zy"  # Replace with a valid token
    test_lot_size = 5  # Example lot size
    test_tp = 3.00        # Example take profit
    test_sl = .50        # Example stop loss
    test_symbol = "CRASH600"  # Example trading symbol

    # Call the executeTrade function
    return executeTrade(test_token, test_lot_size, test_tp, test_sl, test_symbol)

# -----------------------------------------
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import asyncio

@csrf_exempt
async def testContract(request):
    contract_id = '271228658368'
    app_id = "65102"
    api_token = "a1-Rpkn31phHKJihM7NtL3HoMNiOb9zy"

    if request.method == 'POST':
        try:
            # trade = testApp(request)
            updates = await fetch_contract_updates(contract_id, api_token, app_id)
            print(updates)

            # Extracting the correct contract details
            contract_data = updates.get("proposal_open_contract", {})

            display_name = contract_data.get("display_name", "N/A")
            entry_price = float(contract_data.get("entry_spot", 0))
            current_price = float(contract_data.get("current_spot", 0))
                        
            entry_time = contract_data.get("date_settlement")
            current_time = contract_data.get("current_spot_time")

            # If necessary, convert to datetime objects for display purposes:
            entry_time_datetime = datetime.utcfromtimestamp(entry_time)
            current_time_datetime = datetime.utcfromtimestamp(current_time)

            # If you need to send them as strings for any reason, convert to ISO format (optional):
            entry_time_str = entry_time_datetime.isoformat()
            current_time_str = current_time_datetime.isoformat()


            # Extracting stop loss and take profit correctly
            limit_order = contract_data.get("limit_order", {})
            stop_loss = float(limit_order.get("stop_loss", {}).get("value", 0))
            take_profit = float(limit_order.get("take_profit", {}).get("value", 0))

            return JsonResponse({
                "displayName": display_name,
                "entryPrice": entry_price,
                "currentPrice": current_price,
                "stopLoss": stop_loss,
                "takeProfit": take_profit,
                "entryTime":entry_time,
                "currentTime":  current_time
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

# -----------------------------------------


# Async function to get profit table
async def getpt(request):
    # Derive today's date and calculate December 25 of the previous year
    today = datetime.today()
    last_year_dec_25 = datetime(today.year - 1, 12, 25)

    # Format dates as strings in YYYY-MM-DD
    date_to = today.strftime("%Y-%m-%d")
    date_from = last_year_dec_25.strftime("%Y-%m-%d")

    token = "a1-Rpkn31phHKJihM7NtL3HoMNiOb9zy"  # Replace with your authorized API token
    options = {
        "limit": 10,  # Limit to 10 transactions
        "sort": "DESC",  # Sort by most recent transactions
        "description": True,  # Include contract descriptions
        "date_from": date_from,  # Calculated start date
        "date_to": date_to,  # Calculated end date
    }

    try:
        # Fetch profit table and statistics from the Deriv API
        profit_table_response = await fetch_profit_table(token, options)
        
        # Check if 'profit_table' contains valid data
        if not profit_table_response.get("profit_table"):
            return JsonResponse({"message": "No transactions found."}, status=200)
        
        # Prepare the response with profit table data and stats
        response_data = {
            "profit_table": profit_table_response["profit_table"],
            "stats": profit_table_response["stats"]
        }
        return JsonResponse(response_data, safe=False, status=200)

    except Exception as e:
        # Return an error message if there's an exception
        return JsonResponse({"error": str(e)}, status=500)


# -----------------------------------------
