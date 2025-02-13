import asyncio
import json
from deriv_api import DerivAPI
from forex.clickhouse.connection import get_clickhouse_client
from trade.activeTradeFetcher import get_active_trades  # Synchronous version
from trade.completeTradeUpdater import update_trade_status
from concurrent.futures import ThreadPoolExecutor

APP_ID = "65102"
API_TOKEN = "a1-Rpkn31phHKJihM7NtL3HoMNiOb9zy"

async def monitor_trades():
    """
    Continuously fetch active trades and monitor them asynchronously.
    """
    tasks = {}  # Store ongoing tasks for contracts

    while True:
        print("\n[Monitor Trades] Checking for active trades...")

        try:
            active_trades = get_active_trades()  # Call this synchronously
            print(f"[Monitor Trades] Fetched {len(active_trades)} active trades.")
        except Exception as e:
            print(f"[Monitor Trades] Error fetching active trades: {e}")
            await asyncio.sleep(2)
            continue  # Prevent loop break

        trades = [trade['contract_id'] for trade in active_trades]
        print(f"[Monitor Trades] Extracted {len(trades)} contract IDs.")

        for contract_id in trades:
            if contract_id not in tasks:
                print(f"[Monitor Trades] Starting watch task for contract {contract_id}")
                task = asyncio.create_task(watch_contract(contract_id))
                tasks[contract_id] = task
            else:
                print(f"[Monitor Trades] Watch task already exists for contract {contract_id}")

        await asyncio.gather(*tasks.values(), return_exceptions=True)
        print("[Monitor Trades] All tasks finished. Sleeping for 2 seconds.")
        await asyncio.sleep(2)

async def watch_contract(contract_id):
    """
    Watch contract by fetching updates and monitor asynchronously.
    """
    print(f"[Watch Contract] Monitoring contract {contract_id}...")
    
    try:
        await fetch_contract_updates(contract_id, API_TOKEN, APP_ID)
        print(f"[Watch Contract] Successfully fetched updates for contract {contract_id}")
    except Exception as e:
        print(f"[Watch Contract] Error fetching updates for {contract_id}: {e}")


async def fetch_contract_updates(contract_id, api_token, app_id):
    """
    Fetches contract updates continuously until the contract ends.
    """
    print(f"[Fetch Contract Updates] Starting updates for contract {contract_id}...")
    api = DerivAPI(app_id=app_id)
    try:
        print("authorizing")
        await api.authorize(api_token)
        print(f"[Fetch Contract Updates] Authorized successfully for contract {contract_id}.")

        while True:
            try:
                response = await api.send({
                    "proposal_open_contract": 1,
                    "contract_id": contract_id
                })
                
                contract_details = response.get("proposal_open_contract", {})
                print(f"[Fetch Contract Updates] Contract details for ID {contract_id}: {json.dumps(contract_details, indent=4)}")

                buy_price = contract_details.get("buy_price", 0.0)  # Extract buy price
                print(f"[Fetch Contract Updates] Buy price: {buy_price}")

                # Check if the contract has ended (either is_sold or status == "sold")
                if contract_details.get("is_sold") == 1 or contract_details.get("status") == "sold":
                    print(f"[Fetch Contract Updates] Contract {contract_id} has ended. Updating database...")
                    sell_time = contract_details.get("sell_time", "N/A")
                    sell_price = contract_details.get("sell_price", 0.0)
                    profit_loss = contract_details.get("profit", 0.0)
                    
                    await update_trade_status(contract_id, "complete", sell_time, sell_price, profit_loss, buy_price)
                    print(f"[Fetch Contract Updates] Database updated for contract {contract_id}.")
                    break
                else:
                    print(f"[Fetch Contract Updates] Contract {contract_id} is still open. Waiting for updates...")

            except Exception as e:
                print(f"[Fetch Contract Updates] Error fetching contract details for {contract_id}: {e}")
                await asyncio.sleep(5)  # Wait before retrying if an error happens

            await asyncio.sleep(2)  # Non-blocking sleep for 2 seconds
    
    except Exception as e:
        print(f"[Fetch Contract Updates] Authorization error for contract {contract_id}: {e}")
    
    finally:
        await api.disconnect()
        print(f"[Fetch Contract Updates] Disconnected from Deriv API for contract {contract_id}.")
