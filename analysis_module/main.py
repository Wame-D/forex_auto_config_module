import logging
from datetime import datetime, timedelta
import pytz
import asyncio
from .data_fetching import fetch_forex_data
from .data_aggregation import aggregate_data
from .strategy_analysis import analysis
from .risk_management import calculate_risk
from forex.clickhouse.connection import get_clickhouse_client
from trade.views import executeTrade

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define the CAT timezone and ClickHouse client
CAT_TIMEZONE = pytz.timezone("Africa/Harare")
client = get_clickhouse_client()


async def main():
    """
    Main loop for fetching, aggregating, and analyzing forex data.
    Executes every 4 hours.
    """
    while True:
        try:
            now_utc = datetime.utcnow()
            aligned_time = now_utc.replace(second=0, microsecond=0)
            aligned_time_cat = aligned_time.astimezone(CAT_TIMEZONE)

            print(f"\n[INFO] Current UTC Time: {now_utc}")
            print(f"[INFO] Aligned Time (CAT): {aligned_time_cat}")

            # Fetch data
            logging.info("Fetching forex data...")
            df_minute = fetch_forex_data()
            if df_minute is None:
                print("[ERROR] Failed to fetch forex data. Retrying in 60 seconds...")
                await asyncio.sleep(60)
                continue

            print("[INFO] Forex data fetched successfully.")

            # Aggregate data
            print("[INFO] Aggregating data into 4H ,30M and 15M intervals...")
            df_4h = aggregate_data(df_minute, "4H")
            df_15m = aggregate_data(df_minute, "15M")
            df_30m = aggregate_data(df_minute, "30M")
            print("[INFO] Data aggregation complete.")

            # Analyze strategy and generate signals
            print("[INFO] Analyzing trading strategy...")
            #strategy_type = "Malaysian" 
            strategy_type = "Moving Average" 
            signals = analysis(df_4h,df_30m, df_15m, strategy_type)

            if signals:
                save_signals_to_clickhouse(signals)
                await prepare_trading(signals)
            else:
                print("[INFO] No trading signals generated.")

        except Exception as e:
            print(f"[ERROR] Exception in main loop: {e}")
            logging.error(f"Error in main loop: {e}")

        # Sleep for the next interval (4 hours)
        sleep_duration = max(4 * 3600, 0)  # Ensure at least 4 hours
        print(f"[INFO] Sleeping for {sleep_duration // 3600} hours...\n")
        await asyncio.sleep(sleep_duration)


def save_signals_to_clickhouse(signals):
    """
    Save trading signals to a ClickHouse database.
    """
    table_name = "trading_signals"

    try:
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                timestamp DateTime,
                Pair String,
                Signal String,
                Entry Float64,
                SL Float64,
                TP Float64,
                Safe_Zone_Top Float64,
                Safe_Zone_Bottom Float64
            ) ENGINE = MergeTree()
            ORDER BY timestamp
        """
        client.command(create_table_query)
        print("[INFO] Trading signals table created or verified in ClickHouse.")

        logging.info("Storing trading signals in ClickHouse...")
        for signal in signals:
            try:
                client.command(f"""
                    INSERT INTO {table_name} 
                    (timestamp, Pair, Signal, Entry, SL, TP,Safe_Zone_Top, Safe_Zone_Bottom)
                    VALUES (NOW(), '{signal['Pair']}', '{signal['Signal']}', {signal['Entry']}, {signal['SL']}, {signal['TP']}, {signal['Safe Zone Top']}, {signal['Safe Zone Bottom']})
                """)
                print(f"[INFO] Signal stored: {signal}")
            except Exception as e:
                print(f"[ERROR] Failed to store signal: {signal}. Error: {e}")
                logging.error(f"Failed to store signal: {signal}. Error: {e}")

    except Exception as e:
        print(f"[ERROR] Error setting up ClickHouse table or storing signals: {e}")
        logging.error(f"Error setting up ClickHouse table or storing signals: {e}")


async def prepare_trading(signals):
    """
    Prepare and execute trades based on generated signals.
    """
    try:
        strategy = "malysian"
        local_symbol = "frxEURUSD"

        print("[INFO] Preparing trading...")
        result = client.query(f"""
            SELECT token FROM userdetails 
            WHERE strategy = '{strategy}' AND trading = true
        """)

        if not result.result_set:
            print("[WARNING] No active tokens found for the specified strategy.")
            return

        tokens = [row[0] for row in result.result_set]
        print(f"[INFO] Found tokens for trading: {tokens}")

        for signal in signals:
            for token in tokens:
                symbols_result = client.query(f"""
                    SELECT symbol FROM symbols 
                    WHERE token = '{token}'
                """)
                symbols = [row[0] for row in symbols_result.result_set]

                if local_symbol in symbols:
                    print(f"[INFO] Token {token} is linked to symbol {local_symbol}. Calculating risk...")
                    risk_amount = await calculate_risk(token,signal['Entry'],signal['SL'])
                    print(f"[INFO] Risk amount calculated: {risk_amount}")

                    if risk_amount > 0:
                        if signal['Signal'] == "Buy":
                            print(f"[INFO] Placing BUY trade for {local_symbol} with risk amount {risk_amount}")
                            executeTrade(token, risk_amount, signal['TP'], signal['SL'], local_symbol)
                            print("[INFO] BUY trade executed successfully.")
                        elif signal['Signal'] == "Sell":
                            print(f"[INFO] Placing SELL trade for {local_symbol} with risk amount {risk_amount}")
                            executeTrade(token, risk_amount, signal['TP'], signal['SL'], local_symbol)
                            print("[INFO] SELL trade executed successfully.")
                        else:
                            print("[WARNING] Unknown signal type encountered.")
                    else:
                        print(f"[WARNING] Risk amount too low for token {token}. Trade skipped.")
    except Exception as e:
        print(f"[ERROR] Error in prepare_trading: {e}")
        logging.error(f"Error in prepare_trading: {e}")


if __name__ == "__main__":
    asyncio.run(main())
