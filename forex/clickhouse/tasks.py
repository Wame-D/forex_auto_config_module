# from .connection import get_clickhouse_client

# def save_candles_to_clickhouse(candle_data):
#     """
#     Save candle data to ClickHouse.
#     :param candle_data: List of dictionaries with candle data.
#     """
#     client = get_clickhouse_client()

#     # Construct the insert query
#     insert_query = "INSERT INTO candles_table (timestamp, open, high, low, close) VALUES"
#     values = [
#         f"({data['timestamp']}, {data['open']}, {data['high']}, {data['low']}, {data['close']})"
#         for data in candle_data
#     ]
#     client.command(f"{insert_query} {','.join(values)}")
#     print("Candles saved to ClickHouse")

from deriv_api import DerivAPI
import asyncio
from .connection import get_clickhouse_client
from datetime import datetime

async def fetch_and_store_candles():
    """
    Fetch candles from DerivAPI and store them in ClickHouse.
    """
    deriv_app_id = 65102
    symbol = "frxEURUSD"  # Replace with your symbol
    granularity = 60  # Candle timeframe in seconds
    table_name = "candles"  # ClickHouse table

    try:
        # Initialize Deriv API client
        api = DerivAPI({"app_id": deriv_app_id})
        await api.connect()

        # Subscribe to candle data
        response = await api.ticks_history({
            "ticks_history": symbol,
            "granularity": granularity,
            "style": "candles",
            "count": 10,
            "subscribe": 1,  # Continuous subscription
        })

        if "error" in response:
            print(f"Error fetching candles: {response['error']['message']}")
            return

        print("Subscribed to candle data...")

        # Process each incoming candle
        async for candle in response["candles"]:
            await store_candle_in_clickhouse(candle, table_name)

    except Exception as e:
        print(f"Error in fetch_and_store_candles: {e}")
    finally:
        # Ensure the API disconnects
        if api:
            await api.disconnect()

async def store_candle_in_clickhouse(candle, table_name):
    """
    Store a single candle in ClickHouse.
    """
    try:
        # Extract candle data
        epoch = candle["epoch"]
        open_price = candle["open"]
        high_price = candle["high"]
        low_price = candle["low"]
        close_price = candle["close"]

        # Convert epoch to timestamp
        timestamp = datetime.utcfromtimestamp(epoch)

        # Insert into ClickHouse with timestamp as primary key
        client = get_clickhouse_client()
        query = f"""
            INSERT INTO {table_name} (timestamp, open, high, low, close)
            VALUES ('{timestamp}', {open_price}, {high_price}, {low_price}, {close_price})
        """
        client.command(query)
        print(f"Candle stored: {timestamp} - Open: {open_price}, Close: {close_price}")
    except Exception as e:
        print(f"Error storing candle: {e}")

def start_candle_fetcher():
    """
    Start the candle fetching process.
    """
    asyncio.run(fetch_and_store_candles())

