import asyncio
import json
from websocket import create_connection
from deriv_api import DerivAPI
from forex.clickhouse.connection import get_clickhouse_client

def update_trade_status(contract_id, trade_status, sell_time, sell_price, profit_loss):
    """Updates the trade status and additional fields in the ClickHouse database."""
    try:
        client = get_clickhouse_client()
        update_query = f'''
            ALTER TABLE trades UPDATE 
                trade_status = '{trade_status}',
                sell_time = '{sell_time}',
                sell_price = {sell_price},
                profit_loss = {profit_loss}
            WHERE contract_id = {contract_id};
        '''
        client.command(update_query)
        print(f"Trade {contract_id} updated to status: {trade_status}, sell_price: {sell_price}, profit/loss: {profit_loss}")
    except Exception as e:
        print(f"Failed to update trade status: {e}")

async def fetch_contract_updates(contract_id, api_token, app_id):
    """
    Fetches contract updates continuously until the contract ends.
    """
    api = DerivAPI(app_id=app_id)
    try:
        await api.authorize(api_token)
        print("Authorized successfully.")

        while True:
            try:
                response = await api.send({
                    "proposal_open_contract": 1,
                    "contract_id": contract_id
                })
                
                contract_details = response.get("proposal_open_contract", {})
                print(f"Contract details for ID {contract_id}:", json.dumps(contract_details, indent=4))

                if contract_details.get("is_sold") == 1 or contract_details.get("status") == "sold":
                    print("Contract has ended. Updating database...")
                    sell_time = contract_details.get("sell_time", "N/A")
                    sell_price = contract_details.get("sell_price", 0.0)
                    profit_loss = contract_details.get("profit", 0.0)
                    update_trade_status(contract_id, "complete", sell_time, sell_price, profit_loss)
                    break
            
            except Exception as e:
                print(f"Error fetching contract details: {e}")
                break

            await asyncio.sleep(2)
    
    except Exception as e:
        print(f"Authorization error: {e}")
    
    finally:
        await api.disconnect()
        print("Disconnected from Deriv API")
