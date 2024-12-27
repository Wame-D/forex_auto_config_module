# from clickhouse_connect import Client

# # Global client instance
# clickhouse_client = None

# def connect_to_clickhouse():
#     """
#     Establish a connection to the ClickHouse database.
#     """
#     global clickhouse_client
#     if not clickhouse_client:
#         clickhouse_client = Client(
#             host='rerj5p7iz5.europe-west4.gcp.clickhouse.cloud',
#             user='default',
#             password='5u59TMG6u_1Jl',
#             secure=True
#         )
#         print("Result:", client.query("SELECT 1").result_set[0][0])
#         print("Connected to ClickHouse")
#     return clickhouse_client
