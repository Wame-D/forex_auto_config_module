import asyncio
import threading
from datetime import datetime, timedelta
from deriv_api import DerivAPI
import pytz
from .connection import get_clickhouse_client
from analysis_module.main import main
import time

# Constants
DERIV_APP_ID = 65102  # Deriv API app ID
GRANULARITY = 60  # Timeframe for each candle (1 minute granularity)
CAT_TIMEZONE = pytz.timezone("Africa/Harare")  # Central Africa Time for timestamp display
RETRY_ATTEMPTS = 5  # Number of retry attempts in case of failure
RETRY_DELAY = 5  # Delay between retry attempts (in seconds)

# Define a dictionary to map symbols to table names dynamically
symbols_and_tables = {
        "frxEURUSD": "eurousd_candles",
        "frxGBPUSD": "gbpusd_candles",
        "OTC_AS51": "austraila200_candles",
        "frxUSDJPY": "usdjpy_candles",
        "OTC_SPC": "us500_candles",
        "R_75": "v75_candles",
        "frxXAUUSD": "gold_candles"
    }
# Utility function to get aligned UTC time (start of the minute)
def get_aligned_time():
    now_utc = datetime.utcnow()
    return now_utc.replace(second=0, microsecond=0)

# Utility function to handle retry logic when fetching candles
async def fetch_with_retry(api, symbol, aligned_time):
    """
    Fetches candles from DerivAPI with retry logic in case of failures.
    This ensures we get the latest candle for the symbol.
    """
    retries = 0
    while retries < RETRY_ATTEMPTS:
        try:
            response = await api.ticks_history({
                "ticks_history": symbol,
                "granularity": GRANULARITY,
                "style": "candles",
                "start": int(aligned_time.timestamp()),
                "end": int(aligned_time.timestamp()) + GRANULARITY,
                "count": 1,  # We only need the latest candle
            })

            # Handle API error
            if "error" in response:
                print(f"Error fetching candles for {symbol} at {aligned_time}: {response['error']['message']}")
                retries += 1
                time.sleep(RETRY_DELAY)
                continue

            return response.get("candles", [])
        except Exception as e:
            print(f"Error fetching candles for {symbol} at {aligned_time}: {e}")
            retries += 1
            time.sleep(RETRY_DELAY)

    return []  # Return empty if retries exceeded

# Function to store candle data in ClickHouse
async def store_candles_in_clickhouse(candles, table_name, aligned_time):
    try:
        # Connect to the ClickHouse client
        client = get_clickhouse_client()

        # Create the table if it doesn't exist
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

        # Insert multiple candles at once
        insert_query = f"""
            INSERT INTO {table_name} (timestamp, open, high, low, close) VALUES
        """
        values = []
        for candle in candles:
            epoch = candle["epoch"]
            open_price = candle["open"]
            high_price = candle["high"]
            low_price = candle["low"]
            close_price = candle["close"]

            # Convert the epoch timestamp to UTC and then to CAT
            timestamp_utc = datetime.utcfromtimestamp(epoch)
            timestamp_cat = timestamp_utc.astimezone(CAT_TIMEZONE)
            values.append(f"('{timestamp_utc}', {open_price}, {high_price}, {low_price}, {close_price})")

            # Print details of the candle with open, high, low, close prices, and aligned time
            print(f"[{aligned_time}] Candles stored in table {table_name}: "
                  f"[Open: {open_price}, High: {high_price}, Low: {low_price}, Close: {close_price}]")

        insert_query += ", ".join(values)
        client.command(insert_query)

    except Exception as e:
        print(f"Error storing candles for {table_name}: {e}")

# Function to fetch and store candles for a given symbol
async def fetch_and_store(symbol: str, table_name: str, aligned_time):
    """
    Fetch candles for a specific symbol at the aligned time and return them.
    This is done concurrently with other symbols to ensure all candles are fetched at the same time.
    """
    api = DerivAPI(app_id=DERIV_APP_ID)

    # Fetch candles with retry logic
    candles = await fetch_with_retry(api, symbol, aligned_time)

    # Store candles in the corresponding table
    if candles:
        await store_candles_in_clickhouse(candles, table_name, aligned_time)

# Function to fetch all symbols' candles concurrently at the same aligned time
async def fetch_all_candles_at_once(aligned_time):
    """
    Fetch candles for all symbols concurrently for the same aligned minute.
    This function ensures that all candles for all symbols are fetched at the same time.
    """
    # Fetch all candles concurrently for all symbols at the same aligned time
    fetch_tasks = [
        fetch_and_store(symbol, table, aligned_time)
        for symbol, table in symbols_and_tables.items()
    ]
    await asyncio.gather(*fetch_tasks)

# Function to run the entire process for fetching and storing candles concurrently
async def run_fetch_and_store_process():
    """
    This function runs the fetching and storing process in a loop.
    It ensures that candles are fetched for all symbols concurrently at the start of each aligned minute.
    """
    while True:
        aligned_time = get_aligned_time()  # Get aligned time at the start of the minute

        # Fetch and store all candles for all symbols at the same aligned time
        await fetch_all_candles_at_once(aligned_time)

        # Wait until the start of the next minute
        next_minute = aligned_time + timedelta(minutes=1)
        sleep_duration = (next_minute - datetime.utcnow()).total_seconds()
        if sleep_duration > 0:
            await asyncio.sleep(sleep_duration)  # Sleep to align the next fetch with the new minute

# Function to start the candle fetcher in a background thread
def start_candle_fetcher():
    """
    Starts the candle fetching process concurrently in a background thread.
    Each symbol's fetch process is handled concurrently to ensure synchronization.
    """
    def thread_function():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(run_fetch_and_store_process(), main()))

    # Start the background thread
    thread = threading.Thread(target=thread_function)
    thread.start()
