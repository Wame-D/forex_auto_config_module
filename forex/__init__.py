# # from .clickhouse.connection import get_clickhouse_client

# # def initialize_clickhouse():
# #     """
# #     Initialize ClickHouse connection on startup.
# #     """
# #     get_clickhouse_client()

# # # Trigger initialization
# # initialize_clickhouse()
# from .clickhouse.connection import get_clickhouse_client
# from .clickhouse.tasks import start_candle_fetcher
# import threading

# def initialize_clickhouse():
#     """
#     Initialize ClickHouse connection on startup.
#     """
#     get_clickhouse_client()
#     print("ClickHouse connection initialized.")

# def start_candle_fetcher_thread():
#     """
#     Start the candle fetcher in a separate thread.
#     This will fetch candles from the Deriv API and save them to ClickHouse.
#     """
#     threading.Thread(target=start_candle_fetcher, daemon=True).start()
#     print("Started fetching and saving candles in the background.")

# # Trigger initialization
# initialize_clickhouse()

# # Start fetching and saving candles automatically
# start_candle_fetcher_thread()
