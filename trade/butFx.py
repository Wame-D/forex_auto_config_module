from django.shortcuts import render
import websocket
import json

def send_request(ws, request):
    """Sends a request to the WebSocket connection and returns the response."""
    ws.send(json.dumps(request))
    response = ws.recv()
    response_data = json.loads(response)
    if "error" in response_data:
        print(f"Error in response: {response_data['error']}")
    return response_data

def fxBuy(request):
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

    active_symbols_request = {"active_symbols": "full"}
    try:
        active_symbols_response = send_request(ws, active_symbols_request)
        symbols = active_symbols_response.get("active_symbols", [])
    except Exception as e:
        print(f"Failed to fetch available instruments: {e}")
        return render(request, "index.html", {"message": f"Failed to fetch instruments: {e}"})

    symbol = "frxAUDUSD"
    contracts_for_request = {"contracts_for": symbol}
    try:
        contracts_for_response = send_request(ws, contracts_for_request)
        contracts = contracts_for_response.get("contracts_for", {}).get("available", [])
    except Exception as e:
        print(f"Failed to fetch contracts for {symbol}: {e}")
        return render(request, "index.html", {"message": f"Failed to fetch contracts: {e}"})

    proposal_request = {
        "proposal": 1,
        "basis": "stake",
        "contract_type": "MULTUP",
        "currency": "USD",
        "symbol": symbol,
        "amount": 10,
        "multiplier": 30,
        "limit_order": {
            "take_profit": 7.90,
            "stop_loss": 8.32
        }
    }

    try:
        proposal_response = send_request(ws, proposal_request)
        proposal_id = proposal_response.get("proposal", {}).get("id")
        if not proposal_id:
            print("No proposal ID received.")
            return render(request, "index.html", {"message": "Failed to receive proposal ID."})
        print("Proposal received:", proposal_response)
    except Exception as e:
        print(f"Failed to request proposal: {e}")
        return render(request, "index.html", {"message": f"Failed to request proposal: {e}"})

    if proposal_id:
        buy_request = {"buy": proposal_id, "price": 10}
        try:
            buy_response = send_request(ws, buy_request)
            print("Buy response:", buy_response)
            contract_id = buy_response.get("buy", {}).get("contract_id")
            if not contract_id:
                print("Contract purchase failed: No contract ID returned.")
                return render(request, "index.html", {"message": "Contract purchase failed."})
            print("Contract purchased:", buy_response)

            # Monitor contract status
            open_contract_request = {"proposal_open_contract": 1, "contract_id": contract_id, "subscribe": 1}
            try:
                while True:
                    open_contract_response = send_request(ws, open_contract_request)
                    contract_details = open_contract_response.get("proposal_open_contract", {})
                    status = contract_details.get("status")
                    # print("Contract details:", contract_details)

                    if status == "open":
                        print("Contract is Open")
                        break

                    if status == "closed":
                        print("Contract is closed. Exiting monitoring loop.")
                        break

                    # custom logic for handling contract updates here.

            except Exception as e:
                print(f"Failed to monitor contract status continuously: {e}")
                return render(request, "index.html", {"message": f"Failed to monitor contract status: {e}"})

        except Exception as e:
            print(f"Failed to purchase contract: {e}")
            return render(request, "index.html", {"message": f"Failed to purchase contract: {e}"})

    try:
        ws.close()
        print("WebSocket connection closed.")
    except Exception as e:
        print(f"Error closing WebSocket connection: {e}")
        return render(request, "index.html", {"message": f"Error closing WebSocket: {e}"})

    return render(request, "index.html", {"message": "Trade completed successfully!"})
