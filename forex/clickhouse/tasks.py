granularity = 60 
deriv_app_id = 65102

from deriv_api import DerivAPI
from .connection import get_clickhouse_client
from datetime import datetime, timedelta
import pytz  # Import pytz for timezone handling
import asyncio
import threading
import logging

from authorise_deriv.views import balance

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m' 

"""
This method handles stoping and strating of user accounts

when the date they choose to start is today it enables them to start
and vice versa.
"""
async def auto_config():
    client = get_clickhouse_client()
    today_date = datetime.today().date()
    print(f"{BLUE}___________________________________________________________________________________{RESET}")
    print("")
    print(f"{BLUE}Running auto_config at {datetime.now()}{RESET}")
    print("")

    try:
        result = client.query(f"""
            SELECT email, stop_date, start_date
            FROM start_stop_table
        """)

        print(f"Query result: {result.result_set}")  # Debugging

        for row in result.result_set:
            email, stop_date, start_date = row[0], row[1], row[2]

            # Ensure date comparison works
            stop_date = stop_date.date() if isinstance(stop_date, datetime) else stop_date
            start_date = start_date.date() if isinstance(start_date, datetime) else start_date

            if stop_date <= today_date:
                trading = 'false'
                print(f"{GREEN}Disabling trading for {email}{RESET }")
                print("")
                client.command(f"""
                    ALTER TABLE userdetails UPDATE trading_today = {trading}, trading = {trading}
                    WHERE email = '{email}'
                """)
            elif start_date <= today_date:
                trading = 'true'
                print(f"{GREEN}Enabling trading for {email}{RESET }")
                print("")
                client.command(f"""
                    ALTER TABLE userdetails UPDATE trading_today = {trading}, trading = {trading}
                    WHERE email = '{email}'
                """)
            else:
                print(f"No update needed for {email}")

        # Resume trading for all eligible users
        print(f"{YELLOW}Resuming trading for all eligible users{RESET}")
        print("")
        client.command(f"""
            ALTER TABLE userdetails UPDATE trading_today = 'true'
            WHERE trading = 'true'
        """)

        # Update balances
        result1 = client.query(f"""
            SELECT token, email
            FROM userdetails
        """)

        print(f"Balance update query result: {result1.result_set}")  # Debugging

        for row in result1.result_set:
            token, email = row[0], row[1]
            print(f"{BLUE}Updating balance for {email}{RESET}")

            account_balance = await balance(token) 
            client.command(f"""
                ALTER TABLE userdetails UPDATE balance_today = {account_balance}
                WHERE token = '{token}'
            """)

            client.command("""
                CREATE TABLE IF NOT EXISTS balances (
                    timestamp DateTime,
                    balance Float32,
                    email String
                ) ENGINE = MergeTree()
                ORDER BY timestamp
            """)
            print("Balance table created")

            client.command(f"""
                INSERT INTO balances (timestamp, balance, email)
                VALUES (NOW(), {account_balance}, '{email}')
            """)

        print(f"{GREEN}Successfully updated balances.{RESET}")

    except Exception as e:
        print(f"Error running auto_config: {e}")
        raise

    # Sleep before rerunning
    print(f"{BLUE}Sleeping for 2 hours...{RESET}")
    await asyncio.sleep(60 * 2)
    await auto_config()


"""
This method
"""
# startimg candle fetching automatically
def start_candle_fetcher():
    """
    Start the candle fetching process concurrently in a background thread.
    """
    def thread_function():
        # Create a new event loop for the thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async tasks
        loop.run_until_complete(
            asyncio.gather(
                fetch_gold_candles(),
                auto_config(),
            )
        )
        
    # Start the thread to run the async tasks
    thread = threading.Thread(target=thread_function)
    thread.start()
