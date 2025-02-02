import asyncio
import websockets
import json

async def fetch_profit_table(token, limit=1):
    """
    Fetch the latest trade from the Profit Table and calculate trade statistics.

    :param token: Your authorized API token with 'readtrading_information' permission.
    :param limit: The maximum number of transactions to retrieve (default is 1 for latest trade).
    :return: A dictionary containing the latest trade and calculated trade statistics.
    """
    url = "wss://ws.binaryws.com/websockets/v3?app_id=65102"
    

    async with websockets.connect(url) as websocket:
        try:
            # Authenticate
            auth_message = {"authorize": token}
            await websocket.send(json.dumps(auth_message))
            auth_response = await websocket.recv()
            auth_data = json.loads(auth_response)

            if "error" in auth_data:
                raise Exception(f"Authorization failed: {auth_data['error']['message']}")

            print("Authorization successful.")

            # Request Profit Table
            profit_table_message = {
                "profit_table": 1,
                "limit": limit,  # Fetch only the latest trade
                "sort": "DESC",  # Ensure we get the most recent trade first
                "description": 1
            }
            await websocket.send(json.dumps(profit_table_message))

            # Receive Profit Table Response
            profit_table_response = await websocket.recv()
            profit_table_data = json.loads(profit_table_response)

            if "error" in profit_table_data:
                raise Exception(f"Error fetching profit table: {profit_table_data['error']['message']}")

            transactions = profit_table_data.get('profit_table', {}).get('transactions', [])

            if not transactions:
                return {"message": "No trades found."}

            # Get the latest trade
            latest_trade = transactions[0]

            # Extract trade details
            buy_price = latest_trade['buy_price']
            sell_price = latest_trade['sell_price']
            multiplier = float(latest_trade.get('multiplier', 1))  # Default to 1 if not present

            # Calculate Profit/Loss
            profit_or_loss = (sell_price - buy_price) * multiplier
            profit_percentage = (profit_or_loss / (buy_price * multiplier)) * 100 if buy_price > 0 else 0

            trade_stats = {
                "trade_id": latest_trade.get("transaction_id"),
                "buy_price": buy_price,
                "sell_price": sell_price,
                "profit_or_loss": profit_or_loss,
                "profit_percentage": profit_percentage
            }

            return {
                "latest_trade": latest_trade,
                "trade_stats": trade_stats
            }

        except Exception as e:
            return {"error": str(e)}

