import clickhouse_connect
# _clickhouse_client = None

# GREEN = '\033[92m'
# RESET = '\033[0m'

# def get_clickhouse_client():
#     """
#     Returns a new instance of the ClickHouse client for the forex_data database.
#     """
#     global _clickhouse_client
#     if _clickhouse_client is None:
#         _clickhouse_client = clickhouse_connect.get_client(
#             host='109.74.196.98',
#             port = '8123',
#             user='default',
#             password='#00forexd4h',
#             database='forex_data'
#             # secure=True
#         )
#         print(f"Result:", _clickhouse_client.query("SELECT 1").result_set[0][0])
#         print(f"{GREEN }Successfully connected to ClickHouse!{RESET}")
#     return _clickhouse_client
_clickhouse_client = None

def get_clickhouse_client():
    _clickhouse_client = clickhouse_connect.get_client(
        host='109.74.196.98',
        port='8123',
        user='default',
        password='#00forexd4h',
        database='forex_data',
        # secure=True
    )
    return _clickhouse_client

