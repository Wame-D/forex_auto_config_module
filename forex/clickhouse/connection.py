import clickhouse_connect

# Singleton instance of the ClickHouse client
_clickhouse_client = None
GREEN = '\033[92m'
RESET = '\033[0m'  

def get_clickhouse_client():
    """
    Returns a singleton instance of the ClickHouse client.
    """
    global _clickhouse_client
    if _clickhouse_client is None:
        _clickhouse_client = clickhouse_connect.get_client(
            host='109.74.196.98',
            port = '8123',
            user='default',
            database='forex_data',
            # password='#00forexd4h',
            secure=False
        )
        print(f"Result:", _clickhouse_client.query("SELECT 1").result_set[0][0])
        print(f"{GREEN }Successfully connected to ClickHouse!{RESET}")
    return _clickhouse_client


