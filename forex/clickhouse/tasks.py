# Constants
# DERIV_APP_ID = 65102  # Deriv API app ID
# GRANULARITY = 60  # Timeframe for each candle (1 minute granularity)
# CAT_TIMEZONE = pytz.timezone("Africa/Harare")  # Central Africa Time for timestamp display
# RETRY_ATTEMPTS = 5  # Number of retry attempts in case of failure
# RETRY_DELAY = 5  # Delay between retry attempts (in seconds)

granularity = 60 
deriv_app_id = 65102

from deriv_api import DerivAPI
from .connection import get_clickhouse_client
from datetime import datetime, timedelta
import pytz  # Import pytz for timezone handling
import asyncio
import threading
from analysis_module.main import main 
import logging

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m' 

# fetching frxGBPUSD
async def fetch_gbpusd_candles():
    """
    Fetch candles from DerivAPI and store them in ClickHouse.
    Starts at the current time and continues fetching a new candle every minute.
    """
    symbol = "frxGBPUSD"
    table_name = "gbpusd_candles"  # ClickHouse table

    # Define the CAT timezone
    cat_timezone = pytz.timezone("Africa/Harare")

    try:
        # Initialize Deriv API client
        api = DerivAPI(app_id=deriv_app_id)

        while True:
            # Get the current time in UTC and align to the start of the current minute
            now_utc = datetime.utcnow()
            aligned_time = now_utc.replace(second=0, microsecond=0)

            # Convert aligned_time to CAT timezone for display
            aligned_time_cat = aligned_time.astimezone(cat_timezone)

            # Fetch the latest candle data
            response = await api.ticks_history({
                "ticks_history": symbol,
                "granularity": granularity,
                "style": "candles",
                "start": int(aligned_time.timestamp()),
                "end": int(aligned_time.timestamp()) + granularity,
                "count": 1,
            })

            if "error" in response:
                print(f"[{aligned_time_cat}] Error fetching candles: {response['error']['message']}")
            else:
                # Process the single candle
                for candle in response.get("candles", []):
                    await store_candle_in_clickhouse(candle, table_name, cat_timezone)

            # Wait until the next minute starts
            next_minute = aligned_time + timedelta(minutes=1)
            sleep_duration = (next_minute - datetime.utcnow()).total_seconds()
            if sleep_duration > 0:
                await asyncio.sleep(sleep_duration)

    except Exception as e:
        print(f"Error in fetch_and_store_candles: {e}")

# fetching  OTC_AS51
async def fetch_austraila200_candles():
    """
    Fetch candles from DerivAPI and store them in ClickHouse.
    Starts at the current time and continues fetching a new candle every minute.
    """

    symbol = "OTC_AS51"
    table_name = "austraila200_candles"  # ClickHouse table

    # Define the CAT timezone
    cat_timezone = pytz.timezone("Africa/Harare")

    try:
        # Initialize Deriv API client
        api = DerivAPI(app_id=deriv_app_id)

        while True:
            # Get the current time in UTC and align to the start of the current minute
            now_utc = datetime.utcnow()
            aligned_time = now_utc.replace(second=0, microsecond=0)

            # Convert aligned_time to CAT timezone for display
            aligned_time_cat = aligned_time.astimezone(cat_timezone)

            # Fetch the latest candle data
            response = await api.ticks_history({
                "ticks_history": symbol,
                "granularity": granularity,
                "style": "candles",
                "start": int(aligned_time.timestamp()),
                "end": int(aligned_time.timestamp()) + granularity,
                "count": 1,
            })

            if "error" in response:
                print(f"[{aligned_time_cat}] Error fetching candles: {response['error']['message']}")
            else:
                # Process the single candle
                for candle in response.get("candles", []):
                    await store_candle_in_clickhouse(candle, table_name, cat_timezone)

            # Wait until the next minute starts
            next_minute = aligned_time + timedelta(minutes=1)
            sleep_duration = (next_minute - datetime.utcnow()).total_seconds()
            if sleep_duration > 0:
                await asyncio.sleep(sleep_duration)

    except Exception as e:
        print(f"Error in fetch_and_store_candles: {e}")

# fetching us500
async def fetch_us500_candles():
    """
    Fetch candles from DerivAPI and store them in ClickHouse.
    Starts at the current time and continues fetching a new candle every minute.
    """
    symbol = "OTC_SPC"
    table_name = "us500_candles"  # ClickHouse table

    # Define the CAT timezone
    cat_timezone = pytz.timezone("Africa/Harare")

    try:
        # Initialize Deriv API client
        api = DerivAPI(app_id=deriv_app_id)

        while True:
            # Get the current time in UTC and align to the start of the current minute
            now_utc = datetime.utcnow()
            aligned_time = now_utc.replace(second=0, microsecond=0)

            # Convert aligned_time to CAT timezone for display
            aligned_time_cat = aligned_time.astimezone(cat_timezone)

            # Fetch the latest candle data
            response = await api.ticks_history({
                "ticks_history": symbol,
                "granularity": granularity,
                "style": "candles",
                "start": int(aligned_time.timestamp()),
                "end": int(aligned_time.timestamp()) + granularity,
                "count": 1,
            })

            if "error" in response:
                print(f"[{aligned_time_cat}] Error fetching candles: {response['error']['message']}")
            else:
                # Process the single candle
                for candle in response.get("candles", []):
                    await store_candle_in_clickhouse(candle, table_name, cat_timezone)

            # Wait until the next minute starts
            next_minute = aligned_time + timedelta(minutes=1)
            sleep_duration = (next_minute - datetime.utcnow()).total_seconds()
            if sleep_duration > 0:
                await asyncio.sleep(sleep_duration)

    except Exception as e:
        print(f"Error in fetch_and_store_candles: {e}")

# fetching Uero/usd
async def fetch_and_store_candles():
    """
    Fetch candles from DerivAPI and store them in ClickHouse.
    Starts at the current time and continues fetching a new candle every minute.
    """
    symbol = "frxEURUSD"
    table_name = "eurousd_candles"  # ClickHouse table

    # Define the CAT timezone
    cat_timezone = pytz.timezone("Africa/Harare")

    try:
        # Initialize Deriv API client
        api = DerivAPI(app_id=deriv_app_id)

        while True:
            # Get the current time in UTC and align to the start of the current minute
            now_utc = datetime.utcnow()
            aligned_time = now_utc.replace(second=0, microsecond=0)

            # Convert aligned_time to CAT timezone for display
            aligned_time_cat = aligned_time.astimezone(cat_timezone)

            # Fetch the latest candle data
            response = await api.ticks_history({
                "ticks_history": symbol,
                "granularity": granularity,
                "style": "candles",
                "start": int(aligned_time.timestamp()),
                "end": int(aligned_time.timestamp()) + granularity,
                "count": 1,
            })

            if "error" in response:
                print(f"[{aligned_time_cat}] Error fetching candles: {response['error']['message']}")
            else:
                # Process the single candle
                for candle in response.get("candles", []):
                    await store_candle_in_clickhouse(candle, table_name, cat_timezone)

            # Wait until the next minute starts
            next_minute = aligned_time + timedelta(minutes=1)
            sleep_duration = (next_minute - datetime.utcnow()).total_seconds()
            if sleep_duration > 0:
                await asyncio.sleep(sleep_duration)

    except Exception as e:
        print(f"Error in fetch_and_store_candles: {e}")

# fetching us30
async def fetch_usdjpy_candles():
    """
    Fetch candles from DerivAPI and store them in ClickHouse.
    Starts at the current time and continues fetching a new candle every minute.
    """
    symbol = "frxUSDJPY"
    table_name = "usdjpy_candles"  # ClickHouse table

    # Define the CAT timezone
    cat_timezone = pytz.timezone("Africa/Harare")

    try:
        # Initialize Deriv API client
        api = DerivAPI(app_id=deriv_app_id)

        while True:
            # Get the current time in UTC and align to the start of the current minute
            now_utc = datetime.utcnow()
            aligned_time = now_utc.replace(second=0, microsecond=0)

            # Convert aligned_time to CAT timezone for display
            aligned_time_cat = aligned_time.astimezone(cat_timezone)

            # Fetch the latest candle data
            response = await api.ticks_history({
                "ticks_history": symbol,
                "granularity": granularity,
                "style": "candles",
                "start": int(aligned_time.timestamp()),
                "end": int(aligned_time.timestamp()) + granularity,
                "count": 1,
            })

            if "error" in response:
                print(f"[{aligned_time_cat}] Error fetching candles: {response['error']['message']}")
            else:
                # Process the single candle
                for candle in response.get("candles", []):
                    await store_candle_in_clickhouse(candle, table_name, cat_timezone)

            # Wait until the next minute starts
            next_minute = aligned_time + timedelta(minutes=1)
            sleep_duration = (next_minute - datetime.utcnow()).total_seconds()
            if sleep_duration > 0:
                await asyncio.sleep(sleep_duration)

    except Exception as e:
        print(f"Error in fetch_and_store_candles: {e}")

# fetching fetch_v75
async def fetch_v75():
    """
    Fetch candles from DerivAPI and store them in ClickHouse.
    Starts at the current time and continues fetching a new candle every minute.
    """
    symbol = "R_75"
    table_name = "v75_candles"  # ClickHouse table

    # Define the CAT timezone
    cat_timezone = pytz.timezone("Africa/Harare")

    try:
        # Initialize Deriv API client
        api = DerivAPI(app_id=deriv_app_id)

        while True:
            # Get the current time in UTC and align to the start of the current minute
            now_utc = datetime.utcnow()
            aligned_time = now_utc.replace(second=0, microsecond=0)

            # Convert aligned_time to CAT timezone for display
            aligned_time_cat = aligned_time.astimezone(cat_timezone)

            # Fetch the latest candle data
            response = await api.ticks_history({
                "ticks_history": symbol,
                "granularity": granularity,
                "style": "candles",
                "start": int(aligned_time.timestamp()),
                "end": int(aligned_time.timestamp()) + granularity,
                "count": 1,
            })

            if "error" in response:
                print(f"[{aligned_time_cat}] Error fetching candles: {response['error']['message']}")
            else:
                # Process the single candle
                for candle in response.get("candles", []):
                    await store_candle_in_clickhouse(candle, table_name, cat_timezone)

            # Wait until the next minute starts
            next_minute = aligned_time + timedelta(minutes=1)
            sleep_duration = (next_minute - datetime.utcnow()).total_seconds()
            if sleep_duration > 0:
                await asyncio.sleep(sleep_duration)

    except Exception as e:
        print(f"Error in fetch_and_store_candles: {e}")

# fetching GOLD
async def fetch_gold_candles():
    """
    Fetch candles from DerivAPI and store them in ClickHouse.
    Starts at the current time and continues fetching a new candle every minute.
    """
    symbol = "frxXAUUSD"  #frxXAGUSD
    table_name = "gold_candles"  # ClickHouse table

    # Define the CAT timezone
    cat_timezone = pytz.timezone("Africa/Harare")

    try:
        # Initialize Deriv API client
        api = DerivAPI(app_id=deriv_app_id)

        while True:
            # Get the current time in UTC and align to the start of the current minute
            now_utc = datetime.utcnow()
            aligned_time = now_utc.replace(second=0, microsecond=0)

            # Convert aligned_time to CAT timezone for display
            aligned_time_cat = aligned_time.astimezone(cat_timezone)

            # Fetch the latest candle data
            response = await api.ticks_history({
                "ticks_history": symbol,
                "granularity": granularity,
                "style": "candles",
                "start": int(aligned_time.timestamp()),
                "end": int(aligned_time.timestamp()) + granularity,
                "count": 1,
            })

            if "error" in response:
                print(f"[{aligned_time_cat}] Error fetching candles: {response['error']['message']}")
            else:
                # Process the single candle
                for candle in response.get("candles", []):
                    await store_candle_in_clickhouse(candle, table_name, cat_timezone)

            # Wait until the next minute starts
            next_minute = aligned_time + timedelta(minutes=1)
            sleep_duration = (next_minute - datetime.utcnow()).total_seconds()
            if sleep_duration > 0:
                await asyncio.sleep(sleep_duration)

    except Exception as e:
        print(f"Error in fetch_and_store_candles: {e}")

# storing candles
async def store_candle_in_clickhouse(candle, table_name, cat_timezone):
    """
    Store a single candle in ClickHouse and display time in CAT.
    """
    try:
        # Extract candle data
        epoch = candle["epoch"]
        open_price = candle["open"]
        high_price = candle["high"]
        low_price = candle["low"]
        close_price = candle["close"]

        # Convert epoch to timestamp in UTC and then to CAT
        timestamp_utc = datetime.utcfromtimestamp(epoch)
        timestamp_cat = timestamp_utc.astimezone(cat_timezone)

        # Connect to ClickHouse and create the table if it doesn't exist
        client = get_clickhouse_client()
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                timestamp DateTime,
                open Float32,
                high Float32,
                low Float32,
                close Float32
            ) ENGINE = MergeTree()
            ORDER BY timestamp
        """
        client.command(create_table_query)

        # Insert the candle into the table
        insert_query = f"""
            INSERT INTO {table_name} (timestamp, open, high, low, close)
            VALUES ('{timestamp_cat}', {open_price}, {high_price}, {low_price}, {close_price})
        """
        client.command(insert_query)
        # print(f"{GREEN}[{timestamp_cat}] Candle stored: Open: {open_price}, Close: {close_price} in {table_name}{RESET}")
    except Exception as e:
        print(f"Error storing candle: {e}")

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
                fetch_gbpusd_candles(),
                fetch_austraila200_candles(),
                fetch_us500_candles(),
                fetch_and_store_candles(),
                fetch_usdjpy_candles(),
                fetch_v75(),
                fetch_gold_candles(),
                main()
            )
        )
        
    # Start the thread to run the async tasks
    thread = threading.Thread(target=thread_function)
    thread.start()
