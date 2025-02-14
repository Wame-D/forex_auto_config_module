from forex.clickhouse.connection import get_clickhouse_client

def get_active_trades():
    """Fetches all active trades from the database using a new client instance."""
    client = None  # Initialize client
    try:
        client = get_clickhouse_client()  # Create a new client instance for this thread
        query = "SELECT contract_id FROM trades WHERE trade_status = 'active';"
        
        # Execute query and fetch results
        result = client.query(query)
        rows = result.result_rows  # Use .result_rows or .fetchall() if available

        active_trades = [{"contract_id": row[0]} for row in rows]

        print("Active Trades:", active_trades)
        return active_trades
    except Exception as e:
        print(f"Error fetching active trades: {e}")
        return []
    finally:
        if client:
            try:
                client.close()  # Properly close the ClickHouse client if it has a `close()` method
            except AttributeError:
                print("Warning: ClickHouse client does not support `close()`. Skipping cleanup.")
