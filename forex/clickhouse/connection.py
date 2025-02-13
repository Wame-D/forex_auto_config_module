import clickhouse_connect

GREEN = '\033[92m'
RESET = '\033[0m'

def get_clickhouse_client():
    """
    Returns a new instance of the ClickHouse client for the forex_data database.
    """
    # Create a new client instance for each request
    client = clickhouse_connect.get_client(
        host='109.74.196.98',
        port='8123',
        user='default',
        password='#00forexd4h',
        database='forex_data'      
    )
    print(f"{GREEN}Successfully created a new ClickHouse connection!{RESET}")
    return client

