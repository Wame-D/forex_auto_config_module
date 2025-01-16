import logging
from datetime import datetime, timedelta
import pytz
import asyncio

from .data_fetching import fetch_forex_data
from .data_aggregation import aggregate_data
from .strategy_analysis import analyze_malaysian_strategy
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

            # Fetch data
            logging.info("Fetching forex data...")
            df_minute = fetch_forex_data()
            if df_minute is None:
                logging.error("Failed to fetch forex data.")
                await asyncio.sleep(60)
                continue

            # Aggregate data
            df_4h = aggregate_data(df_minute, "4H")
            df_15m = aggregate_data(df_minute, "15M")

            # Analyze strategy and generate signals
            logging.info("Analyzing strategy...")
            signals = analyze_malaysian_strategy(df_4h, df_15m)

            if signals:
                logging.info(f"Generated trading signals: {signals}")
                save_signals_to_clickhouse(signals)
                await prepare_trading(signals)
            else:
                logging.info("No trading signals generated.")

        except Exception as e:
            logging.error(f"Error in main loop: {e}")

        # Sleep for the next interval (4 hours)
        sleep_duration = max(4 * 3600, 0)  # Ensure at least 4 hours
        logging.info(f"Sleeping for {sleep_duration // 3600} hours...")
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
                Risk_Amount Float64,
                Position_Size Float64,
                Safe_Zone_Top Float64,
                Safe_Zone_Bottom Float64
            ) ENGINE = MergeTree()
            ORDER BY timestamp
        """
        client.command(create_table_query)

        logging.info("Storing trading signals in ClickHouse...")
        for signal in signals:
            try:
                client.command(f"""
                    INSERT INTO {table_name} 
                    (timestamp, Pair, Signal, Entry, SL, TP, Risk_Amount, Position_Size, Safe_Zone_Top, Safe_Zone_Bottom)
                    VALUES (NOW(), '{signal['Pair']}', '{signal['Signal']}', {signal['Entry']}, {signal['SL']}, {signal['TP']},
                            {signal['Risk Amount']}, {signal['Position Size']}, {signal['Safe Zone Top']}, {signal['Safe Zone Bottom']})
                """)
                logging.info(f"Signal stored: {signal}")
            except Exception as e:
                logging.error(f"Failed to store signal: {signal}. Error: {e}")

    except Exception as e:
        logging.error(f"Error setting up ClickHouse table or storing signals: {e}")


async def prepare_trading(signals):
    """
    Prepare and execute trades based on generated signals.
    """
    try:
        strategy = "malaysian"
        local_symbol = "frxEURUSD"

        result = client.query(f"""
            SELECT token FROM userdetails 
            WHERE strategy = '{strategy}' AND trading = true
        """)

        if not result.result_set:
            logging.warning("No active tokens found for strategy.")
            return

        tokens = [row[0] for row in result.result_set]

        for signal in signals:
            for token in tokens:
                symbols_result = client.query(f"""
                    SELECT symbol FROM symbols 
                    WHERE token = '{token}'
                """)
                symbols = [row[0] for row in symbols_result.result_set]

                if local_symbol in symbols:
                    risk_amount = await calculate_risk(token)
                    if risk_amount > 0:
                        if signal['Signal'] == "Buy":
                            logging.info(f"Placing BUY trade for {local_symbol}")
                            executeTrade(token, risk_amount, signal['TP'], signal['SL'], local_symbol)
                        elif signal['Signal'] == "Sell":
                            logging.info(f"Placing SELL trade for {local_symbol}")
                            executeTrade(token, risk_amount, signal['TP'], signal['SL'], local_symbol)
                        else:
                            logging.warning("Unknown signal type.")
                    else:
                        logging.warning(f"Risk amount too low for token {token}, skipping trade.")
    except Exception as e:
        logging.error(f"Error in prepare_trading: {e}")
if __name__ == "__main__":
    asyncio.run(main())
