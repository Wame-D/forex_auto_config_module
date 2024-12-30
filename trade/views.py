from django.shortcuts import render
import websocket
import json

def send_request(ws, request):
    """Sends a request to the WebSocket connection and returns the response."""
    ws.send(json.dumps(request))
    response = ws.recv()
    return json.loads(response)

def main():
    # Assumptions:
    # 1. You have a valid Deriv API token with the `trading` scope enabled.
    # 2. WebSocket connection is used for real-time communication with the API.
    # 3. Replace `YOUR_API_TOKEN` with your actual API token.

    # Step 1: Establish a WebSocket connection
    url = "wss://ws.binaryws.com/websockets/v3?app_id=65102"
    ws = websocket.create_connection(url)

    # Step 2: Authorize
    token = "a1-PKLDfBJiVcn57wqKSC5TPNQvBhlvK"  # Replace with your API token
    authorize_request = {"authorize": token}
    auth_response = send_request(ws, authorize_request)
    if auth_response.get("error"):
        print("Authorization failed:", auth_response["error"])
        return
    print("Authorization successful")

    # Step 3: Fetch Available Instruments
    active_symbols_request = {"active_symbols": "full"}
    active_symbols_response = send_request(ws, active_symbols_request)
    symbols = active_symbols_response.get("active_symbols", [])
    print("Available instruments:", [symbol["symbol"] for symbol in symbols])

    # Step 4: Get Contract Details for a specific symbol
    symbol = "R_100"  # Replace with your desired symbol
    contracts_for_request = {"contracts_for": symbol}
    contracts_for_response = send_request(ws, contracts_for_request)
    contracts = contracts_for_response.get("contracts_for", {}).get("available", [])
    print(f"Contracts available for {symbol}:", contracts)

    # Step 5: Request a Price (Proposal)
    proposal_request = {
        "proposal": 1,
        "amount": 10,
        "basis": "stake",
        "contract_type": "MULTUP",  # Set to "MULTUP" or "MULTDOWN"
        "currency": "USD",
        "duration": 5,
        "duration_unit": "t",
        "symbol": symbol,
        "limit_order": {
            "take_profit": 150,  # Optional: Take profit limit
            "stop_loss": 130    # Optional: Stop loss limit
        },
        "cancellation": "60m"  # Optional: Deal cancellation within 60 minutes
    }
    proposal_response = send_request(ws, proposal_request)
    proposal_id = proposal_response.get("proposal", {}).get("id")
    print("Proposal received:", proposal_response)

    # Step 6: Buy the Contract
    if proposal_id:
        buy_request = {"buy": proposal_id, "price": 10}
        buy_response = send_request(ws, buy_request)
        contract_id = buy_response.get("buy", {}).get("contract_id")
        print("Contract purchased:", buy_response)

        # Step 7: Monitor the Contract Status
        if contract_id:
            open_contract_request = {"proposal_open_contract": 1, "contract_id": contract_id}
            open_contract_response = send_request(ws, open_contract_request)
            print("Contract status:", open_contract_response)

            # Step 8: Close the Contract Early (if needed)
            sell_request = {"sell": contract_id, "price": 5}  # Adjust price if needed
            sell_response = send_request(ws, sell_request)
            print("Contract sold:", sell_response)

    # Close the WebSocket connection
    ws.close()

if __name__ == "__main__":
    main()

