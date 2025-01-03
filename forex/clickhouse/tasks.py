from deriv_api import DerivAPI
import asyncio
from .connection import get_clickhouse_client
from datetime import datetime, timedelta
import pytz  # Import pytz for timezone handling

async def fetch_and_store_candles():
    """
    Fetch candles from DerivAPI and store them in ClickHouse.
    Starts at the current time and continues fetching a new candle every minute.
    """
    deriv_app_id = 65102
    symbol = "frxEURUSD"
    granularity = 60  # Candle timeframe in seconds
    table_name = "candles"  # ClickHouse table

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
                timestamp DateTime PRIMARY KEY,
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
            VALUES ('{timestamp_utc}', {open_price}, {high_price}, {low_price}, {close_price})
        """
        client.command(insert_query)
        print(f"[{timestamp_cat}] Candle stored: Open: {open_price}, Close: {close_price}")
    except Exception as e:
        print(f"Error storing candle: {e}")

def start_candle_fetcher():
    """
    Start the candle fetching process.
    """
    asyncio.run(fetch_and_store_candles())
