import websockets
import json
from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi
# @swagger_auto_schema(method='post', 
#     request_body=openapi.Schema(
#         type=openapi.TYPE_OBJECT,
#         properties={
#             'token': openapi.Schema(type=openapi.TYPE_STRING),
#         }
#     )
# )
# Authenticate
async def fetch_profit_table(token, limit):
    """
    Fetch the Profit Table from the Deriv API and calculate trade statistics.

    :param token: Your authorized API token with 'readtrading_information' permission.
    :param options: Optional dictionary for profit table request parameters.
                    - limit (int): The maximum number of transactions to retrieve (default is 50).
                    - sort (str): Sorting order ('ASC' or 'DESC', default is 'DESC').
                    - description (bool): Whether to include full contract descriptions (default is False).
                    - date_from (str): Start date (optional).
                    - date_to (str): End date (optional).
    :return: A dictionary containing the profit table and calculated trade statistics.
    """
    # Default options
    options = options or {}
    limit = options.get("limit", {limit})
    sort = options.get("sort", "DESC")
    description = 1 if options.get("description", False) else 0
    date_from = options.get("date_from", "")
    date_to = options.get("date_to", "")

    # Deriv WebSocket URL
    url = "wss://ws.binaryws.com/websockets/v3?app_id=65102"

    # WebSocket connection
    async with websockets.connect(url) as websocket:
        # Authenticate
        auth_message = {
            "authorize": token
        }
        await websocket.send(json.dumps(auth_message))

        # Wait for the authorization response
        auth_response = await websocket.recv()
        auth_data = json.loads(auth_response)
        if "error" in auth_data:
            raise Exception(f"Authorization failed: {auth_data['error']['message']}")

        print("Authorization successful.")

        #  Request Profit Table
        profit_table_message = {
            "profit_table": 1,
            "limit": limit,
            "sort": sort,
            "description": description,
            "date_from": date_from,
            "date_to": date_to
        }
        await websocket.send(json.dumps(profit_table_message))

        # Wait for the profit table response
        profit_table_response = await websocket.recv()
        profit_table_data = json.loads(profit_table_response)

        # print(profit_table_data)

        # Check if there's an error in the response
        if "error" in profit_table_data:
            raise Exception(f"Error fetching profit table: {profit_table_data['error']['message']}")

        # Step 3: Calculate trade statistics
        total_trades = profit_table_data['profit_table']['count']
        transactions = profit_table_data['profit_table']['transactions']
        
        trades_in_profit = 0
        trades_lost = 0
        total_profit = 0
        total_loss = 0
        profit_percentages = []
        loss_percentages = []
        
        for transaction in transactions:
            buy_price = transaction['buy_price']
            sell_price = transaction['sell_price']
            multiplier = float(transaction['multiplier'])
            if buy_price > 0 :
                # Calculate profit or loss for each trade
                profit_or_loss = (sell_price - buy_price) * multiplier

                if profit_or_loss > 0:
                    trades_in_profit += 1
                    total_profit += profit_or_loss
                    profit_percentage = (profit_or_loss / (buy_price * multiplier)) * 100
                    profit_percentages.append(profit_percentage)
                else:
                    trades_lost += 1
                    total_loss += abs(profit_or_loss)
                    loss_percentage = (abs(profit_or_loss) / (buy_price * multiplier)) * 100
                    loss_percentages.append(loss_percentage)

                # Calculate averages
                avg_profit_percentage = sum(profit_percentages) / len(profit_percentages) if profit_percentages else 0
                avg_loss_percentage = sum(loss_percentages) / len(loss_percentages) if loss_percentages else 0

                # Calculate overall profit/loss
                total_net_profit_loss = total_profit - total_loss
                win_percentage = (trades_in_profit / total_trades) * 100
                loss_percentage = (trades_lost / total_trades) * 100

                # Trade stats
                stats = {
                    "total_trades": total_trades,
                    "trades_in_profit": trades_in_profit,
                    "trades_lost": trades_lost,
                    "total_profit": total_profit,
                    "total_loss": total_loss,
                    "avg_profit_percentage": avg_profit_percentage,
                    "avg_loss_percentage": avg_loss_percentage,
                    "win_percentage": win_percentage,
                    "loss_percentage": loss_percentage,
                    "total_net_profit_loss": total_net_profit_loss
                }

                # Return the profit table data and calculated statistics
                return {
                    "profit_table": profit_table_data.get("profit_table", {}),
                    "stats": stats
                }
