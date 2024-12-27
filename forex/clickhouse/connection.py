# from clickhouse_connect import Client
import clickhouse_connect

# Singleton instance of the ClickHouse client
_clickhouse_client = None

def get_clickhouse_client():
    """
    Returns a singleton instance of the ClickHouse client.
    """
    global _clickhouse_client
    if _clickhouse_client is None:
        _clickhouse_client = clickhouse_connect.get_client(
            host='rerj5p7iz5.europe-west4.gcp.clickhouse.cloud',
            user='default',
            password='5u59TMG6u_1Jl',
            secure=True
        )
        print("Result:", _clickhouse_client.query("SELECT 1").result_set[0][0])
        print("Result:", _clickhouse_client.query("SELECT 1").result_set[0][0])
        print("Successfully connected to ClickHouse!")
    return _clickhouse_client
