import asyncio
import json
from deriv_api import DerivAPI
from forex.clickhouse.connection import get_clickhouse_client
from trade.activeTradeFetcher import get_active_trades
from trade.completeTradeUpdater import update_trade_status

API_TOKEN = "your_api_token"  # Global API token
APP_ID = "your_app_id"  # Global App ID

async def fetch_contract_updates(contract_id):
    """
    Fetches contract updates continuously until the contract ends.
    """
    api = DerivAPI(app_id=APP_ID)
    try:
        await api.authorize(API_TOKEN)
        print(f" Authorized successfully for contract {contract_id}.")

        while True:
            try:
                print(f" Checking updates for contract {contract_id}...")
                response = await api.send({
                    "proposal_open_contract": 1,
                    "contract_id": contract_id
                })
                
                contract_details = response.get("proposal_open_contract", {})
                print(f" Contract details for {contract_id}:\n{json.dumps(contract_details, indent=4)}")

                buy_price = contract_details.get("buy_price", 0.0)

                if contract_details.get("is_sold") == 1 or contract_details.get("status") == "sold":
                    print(f" Contract {contract_id} has ended. Updating database...")
                    sell_time = contract_details.get("sell_time", "N/A")
                    sell_price = contract_details.get("sell_price", 0.0)
                    profit_loss = contract_details.get("profit", 0.0)
                    
                    update_trade_status(contract_id, "complete", sell_time, sell_price, profit_loss, buy_price)
                    print(f" Trade {contract_id} updated successfully.")
                    break
            
            except Exception as e:
                print(f" Error fetching contract {contract_id}: {e}")
                break

            await asyncio.sleep(2)
    
    except Exception as e:
        print(f" Authorization error for contract {contract_id}: {e}")
    
    finally:
        await api.disconnect()
        print(f"🔌 Disconnected from Deriv API for contract {contract_id}.")

async def monitor_trades():
    """
    Continuously fetch active trades and monitor them.
    """
    monitored_trades = set()  # Keep track of trades being monitored

    while True:
        print(" Checking for new active trades...")
        active_trades = get_active_trades()
        new_trades = [trade['contract_id'] for trade in active_trades if trade['contract_id'] not in monitored_trades]

        if new_trades:
            print(f" New trades found: {new_trades}")
            tasks = [fetch_contract_updates(contract_id) for contract_id in new_trades]
            asyncio.create_task(asyncio.gather(*tasks))
            monitored_trades.update(new_trades)
        else:
            print(" No new trades found. Checking again soon...")

        await asyncio.sleep(10)  # Wait before checking for new trades again

# if __name__ == "__main__":
#     print("Starting trade monitoring service...")
#     asyncio.run(monitor_trades())
