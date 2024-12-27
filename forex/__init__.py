from .clickhouse.connection import get_clickhouse_client

def initialize_clickhouse():
    """
    Initialize ClickHouse connection on startup.
    """
    get_clickhouse_client()

# Trigger initialization
initialize_clickhouse()
