import clickhouse_connect

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

