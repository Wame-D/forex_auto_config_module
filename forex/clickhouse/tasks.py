from .connection import get_clickhouse_client

def save_candles_to_clickhouse(candle_data):
    """
    Save candle data to ClickHouse.
    :param candle_data: List of dictionaries with candle data.
    """
    client = get_clickhouse_client()

    # Construct the insert query
    insert_query = "INSERT INTO candles_table (timestamp, open, high, low, close) VALUES"
    values = [
        f"({data['timestamp']}, {data['open']}, {data['high']}, {data['low']}, {data['close']})"
        for data in candle_data
    ]
    client.command(f"{insert_query} {','.join(values)}")
    print("Candles saved to ClickHouse")
