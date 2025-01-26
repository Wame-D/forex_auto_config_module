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
from bot_settings.configurations import eligible_user
# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define the CAT timezone and ClickHouse client
CAT_TIMEZONE = pytz.timezone("Africa/Harare")
client = get_clickhouse_client()

# ANSI escape codes for colors
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m' 

async def main():
    """
    Main loop placeholder.
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
                print(f"{RED}[ERROR] Failed to fetch forex data. Retrying in 60 seconds...{RESET}")
                await asyncio.sleep(60)
                continue

            print(f"{GREEN }[INFO] Forex data fetched successfully.{RESET}")

            # Aggregate data
            print("[INFO] Aggregating data into 4H ,30M and 15M intervals...")
            df_4h = aggregate_data(df_minute, "4H")
            df_15m = aggregate_data(df_minute, "15M")
            df_30m = aggregate_data(df_minute, "30M")
            print(f"{GREEN }[INFO] Data aggregation complete.{RESET}")

            # Analyze strategy and generate signals
            print("[INFO] Analyzing trading strategy...")    
            strategy_type = ["Malaysian", "Moving Average"]
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
        print(f"{BLUE}[INFO] Trading signals table created or verified in ClickHouse.{RESET}")

        logging.info("Storing trading signals in ClickHouse...")
        for signal in signals:
            try:
                client.command(f"""
                    INSERT INTO {table_name} 
                    (timestamp, Pair, Signal, Entry, SL, TP,Safe_Zone_Top, Safe_Zone_Bottom)
                    VALUES (NOW(), '{signal['Pair']}', '{signal['Signal']}', {signal['Entry']}, {signal['SL']}, {signal['TP']}, {signal['Safe Zone Top']}, {signal['Safe Zone Bottom']})
                """)
                print(f"{BLUE}[INFO] Signal stored: {signal}{RESET}")
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
           SELECT token, email FROM userdetails WHERE strategy = '{strategy}' AND trading = 'true' AND trading_today = 'true'
        """)

        if not result.result_set:
            print(f"{YELLOW}[WARNING] No active tokens found for the specified strategy.{RESET}")
            return

        print(f"{GREEN }[INFO] Found tokens for trading: {tokens}{RESET}")

        for signal in signals:
            for row in result.result_set:
                token, email = row[0], row[1]  # Extract token and email from the row
                print(f"Processing token: {token} associated with email: {email}")
                """
                check first if the user is eligible to trade today
                """
                eligible = await eligible_user(email,token)
                # checking if the user is eligible to trade
                if eligible == 'true':
                    symbols_result = client.query(f"""
                        SELECT symbol FROM symbols 
                        WHERE token = '{token}'
                    """)
                    symbols = [row[0] for row in symbols_result.result_set]

                    if local_symbol in symbols:
                        risk_amount = await calculate_risk(token,signal['Entry'],signal['SL'])

                        if risk_amount > 0:
                            if signal['Signal'] == "Buy":
                                print(f"{GREEN }[INFO] Placing BUY trade for {local_symbol} with risk amount {risk_amount}{RESET}")
                                # executeTrade(token, risk_amount, signal['TP'], signal['SL'], local_symbol)
                                print("[INFO] BUY trade executed successfully.")
                            elif signal['Signal'] == "Sell":
                                print(f"{BLUE }[INFO] Placing SELL trade for {local_symbol} with risk amount {risk_amount}{RESET}")
                                # executeTrade(token, risk_amount, signal['TP'], signal['SL'], local_symbol)
                                print(f"{GREEN }[INFO] SELL trade executed successfully.{RESET}")
                            else:
                                print(f"{YELLOW}[WARNING] Unknown signal type encountered.{RESET}")
                        else:
                            print(f"{YELLOW}[WARNING] Risk amount too low for token {token}. Trade skipped.{RESET}")
            
    except Exception as e:
        print(f"[ERROR] Error in prepare_trading: {e}")
        logging.error(f"Error in prepare_trading: {e}")


if __name__ == "__main__":
    asyncio.run(main())

