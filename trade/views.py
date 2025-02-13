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

from .buyAndSell import fxTradeMultiplier

from trade.continuousTradeMonitor import monitor_trades  # Import the monitoring function

async def test_monitor_trades(request):
    """
    Django async view to start monitoring active trades.
    """
    try:
        print("Starting trade monitoring via Django route...")

        # Await the coroutine properly
        await monitor_trades()

        return JsonResponse({"message": "Trade monitoring started successfully."})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


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
# Async function to fetch contract updates
async def testContract(request):
    """
    Django async view to fetch contract updates and display them as HTML.
    """
    contract_id = '271524684528'
    app_id = "65102"
    api_token = "a1-Rpkn31phHKJihM7NtL3HoMNiOb9zy"

    try:
        # Fetch contract updates
        updates = await fetch_contract_updates(contract_id, api_token, app_id)

        # Convert updates to HTML content
        html_content = "<h1>Contract Updates</h1><ul>"
        if isinstance(updates, list):  # If updates are available
            for update in updates:
                html_content += f"<li>{update}</li>"
        elif isinstance(updates, dict) and 'error' in updates:  # If an error occurred
            html_content += f"<li>Error: {updates['error']}</li>"
        else:
            html_content += "<li>No updates or error message received.</li>"

        html_content += "</ul>"

        # Return the HTML response
        return HttpResponse(html_content, content_type="text/html")

    except Exception as e:
        # Handle exceptions and return an error response
        error_message = str(e)
        return HttpResponse(f"<h1>Error: {error_message}</h1>", content_type="text/html")

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
