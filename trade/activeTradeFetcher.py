from forex.clickhouse.connection import get_clickhouse_client

def get_active_trades():
    """Fetches all active trades from the database."""
    try:
        client = get_clickhouse_client()
        query = "SELECT contract_id FROM trades WHERE trade_status = 'active';"
        
        result = client.query(query)  # Execute query
        
        # Fetch results as a list
        rows = result.result_rows  # Use .result_rows or .fetchall() if available

        active_trades = [{"contract_id": row[0]} for row in rows]
        
        print("Active Trades:", active_trades)  # Debugging output
        return active_trades
    except Exception as e:
        print(f"Error fetching active trades: {e}")
        return []
