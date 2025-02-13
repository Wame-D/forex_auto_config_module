import asyncio
from django.http import JsonResponse
from django.shortcuts import render
from django.http import HttpResponse
import asyncio
import websockets
import json
from websocket import create_connection
from deriv_api import DerivAPI
from forex.clickhouse.connection import get_clickhouse_client




def send_request(ws, request):
    """Sends a request to the WebSocket connection and returns the response."""
    ws.send(json.dumps(request))
    response = ws.recv()
    response_data = json.loads(response)
    if "error" in response_data:
        print(f"Error in response: {response_data['error']}")
    return response_data

def fxTradeMultiplier(url, token, symbol, amount, multiplier, take_profit, stop_loss):
    # Establish WebSocket connection
    try:
        ws = create_connection(url)
        print("WebSocket connection established.")
    except Exception as e:
        print(f"Failed to establish WebSocket connection: {e}")
        return {"message": f"Connection failed: {e}"}

    # Authorize with the token
    authorize_request = {"authorize": token}
    try:
        auth_response = send_request(ws, authorize_request)
        if auth_response.get("error"):
            return {"message": f"Authorization failed: {auth_response['error']['message']}"}
        print("Authorization successful.")
    except Exception as e:
        return {"message": f"Authorization failed: {e}"}

    # Request active symbols
    active_symbols_request = {"active_symbols": "full"}
    try:
        symbols_response = send_request(ws, active_symbols_request)
        symbols = symbols_response.get("active_symbols", [])
        print("Active symbols fetched.")
    except Exception as e:
        return {"message": f"Failed to fetch symbols: {e}"}

    # Request contract details for the symbol
    contracts_for_request = {"contracts_for": symbol}
    try:
        contracts_response = send_request(ws, contracts_for_request)
        contracts = contracts_response.get("contracts_for", {}).get("available", [])
    except Exception as e:
        return {"message": f"Failed to fetch contracts: {e}"}

    # Send proposal request
    proposal_request = {
        "proposal": 1,
        "basis": "stake",
        "contract_type": "MULTUP",
        "currency": "USD",
        "symbol": symbol,
        "amount": amount,
        "multiplier": multiplier,
        "limit_order": {
            "take_profit": take_profit * 3,
            "stop_loss": stop_loss + 2.49,
        }
    }

    try:
        print(proposal_request)
        proposal_response = send_request(ws, proposal_request)
        proposal_id = proposal_response.get("proposal", {}).get("id")
        if not proposal_id:
            error_code = proposal_response.get("error", {}).get("code", "Unknown error code")
            error_message = proposal_response.get("error", {}).get("message", "Unknown error message")
            return {"message": f"Failed to receive proposal ID. Error code: {error_code}, Message: {error_message}"}
        print("Proposal received:", proposal_response)
    except Exception as e:
        return {"message": f"Failed to request proposal: {str(e)}"}


    # Execute buy request if proposal ID exists
    if proposal_id:
        buy_request = {"buy": proposal_id, "price": amount}
        try:
            buy_response = send_request(ws, buy_request)
            print("Buy response:", buy_response)
            contract_id = buy_response.get("buy", {}).get("contract_id")
            if not contract_id:
                return {"message": "Contract purchase failed."}
            print("Contract purchased:", contract_id)

            # Monitor contract status
            open_contract_request = {"proposal_open_contract": 1, "contract_id": contract_id, "subscribe": 1}
            try:
                while True:
                    open_contract_response = send_request(ws, open_contract_request)
                    contract_details = open_contract_response.get("proposal_open_contract", {})
                    status = contract_details.get("status")

                    if status == "open":
                        print("Contract is Open")
                        break

                    if status == "closed":
                        print("Contract is closed. Exiting monitoring loop.")
                        break

            except Exception as e:
                return {"message": f"Failed to monitor contract status: {e}"}

        except Exception as e:
            return {"message": f"Failed to purchase contract: {e}"}

    # Close the WebSocket connection
    try:
        ws.close()
        print("WebSocket connection closed.")
        # Connect to ClickHouse and create the table if it doesn't exist
        client = get_clickhouse_client()
       
        # drop_table_query = "DROP TABLE IF EXISTS trades;"
        # client.command(drop_table_query)
        # delete_query = "TRUNCATE TABLE trades;"
        # client.command(delete_query)

        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS trades (
                timestamp Nullable(DateTime),
                contract_id Int128,  -- Required (not nullable)
                token Nullable(String),
                trade_status Nullable(String),
                symbol Nullable(String),
                amount Nullable(Float32),
                take_profit Nullable(Float32),
                stop_loss Nullable(Float32),
                contract_type Nullable(String),
                sell_time Nullable(DateTime),
                buy_price Nullable(Float32),
                sell_price Nullable(Float32),
                profit_loss Nullable(Float32),
                currency Nullable(String),
                multiplier Nullable(Float32)
            ) ENGINE = MergeTree()
            ORDER BY contract_id;
        """

        client.command(create_table_query)

        # Insert the candle into the table
        insert_query = f"""
            INSERT INTO trades (contract_id, token, trade_status, symbol, amount, take_profit, stop_loss,timestamp,currency,contract_type,multiplier)
            VALUES ({contract_id}, '{token}', 'active', '{symbol}', {amount}, {take_profit}, {stop_loss}, NOW(),'usd','MULTUP',{multiplier});
        """
        client.command(insert_query)
        print(f"----------------------------------------------------------- {contract_id} token is {token} trade status : Active, amount {amount}, takeprofit = {take_profit} stoploss = {stop_loss}")
    except Exception as e:
        return {"message": f"Error closing WebSocket: {e}"}
    return {"message": f"Trade completed successfully! Here is the contract ID: {contract_id}"}

def fxCloseMultiplierTrade(request):
    # Sell the contract (close the position)
    try:
        url = "wss://ws.binaryws.com/websockets/v3?app_id=65102"
        ws = websocket.create_connection(url)
        print("WebSocket connection established.")
    except Exception as e:
        print(f"Failed to establish WebSocket connection: {e}")
        return render(request, "index.html", {"message": f"Authorization failed: {e}"})
    
    token = "a1-Rpkn31phHKJihM7NtL3HoMNiOb9zy"  # Replace with your API token
    authorize_request = {"authorize": token}
    try:
        auth_response = send_request(ws, authorize_request)
        if auth_response.get("error"):
            print("Authorization failed:", auth_response["error"])
            return render(request, "index.html", {"message": f"Authorization failed: {auth_response['error']}"} )
        print("Authorization successful")
    except Exception as e:
        print(f"Authorization request failed: {e}")
        return render(request, "index.html", {"message": f"Authorization request failed: {e}"})
        
    sell_request = {"sell": 267924162408, "price": 40}
    try:
        sell_response = send_request(ws, sell_request)
        print("Sell response:", sell_response)
        if sell_response.get("sell", {}).get("msg_type") == "sell":
            print("Contract successfully sold.")
        else:
            print("Failed to sell the contract:", sell_response)
            return render(request, "index.html", {"message": "Failed to sell the contract."})
    except Exception as e:
        print(f"Failed to sell contract: {e}")
        return render(request, "index.html", {"message": f"Failed to sell contract: {e}"})
    
    try:
        ws.close()
        print("WebSocket connection closed.")
    except Exception as e:
        print(f"Error closing WebSocket connection: {e}")
        return render(request, "index.html", {"message": f"Error closing WebSocket: {e}"})
