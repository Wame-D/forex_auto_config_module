from django.http import JsonResponse
from django.shortcuts import render
import websocket
from websocket import create_connection

import json

def send_request(ws, request):
    """Sends a request to the WebSocket connection and returns the response."""
    ws.send(json.dumps(request))
    response = ws.recv()
    response_data = json.loads(response)
    if "error" in response_data:
        print(f"Error in response: {response_data['error']}")
    return response_data


# Testing FUNCTION
def executeTrade(token, lot_size, tp, sl, symbol):
    # Define the proposal details
    proposal_details = {
        "url": "wss://ws.binaryws.com/websockets/v3?app_id=65102",
        "token": token, 
        "symbol": symbol,
        "amount": lot_size,  
        "multiplier": 30, 
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
            return {"message": "Failed to receive proposal ID."}
        print("Proposal received:", proposal_response)
    except Exception as e:
        return {"message": f"Failed to request proposal: {e}"}

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
    except Exception as e:
        return {"message": f"Error closing WebSocket: {e}"}

    return {"message": "Trade completed successfully!"}


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