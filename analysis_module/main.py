import logging
from datetime import datetime
import pytz
import asyncio
from typing import List, Dict, Any, Optional
from .data_fetching import fetch_forex_data
from .data_aggregation import aggregate_data
from .risk_management import calculate_risk
from forex.clickhouse.connection import get_clickhouse_client
from trade.views import executeTrade
from bot_settings.configurations import eligible_user
from .malaysian_strategy_module import malaysian_strategy
from .moving_average_strategy_module import moving_average_strategy
from .constants import CAT_TIMEZONE ,SYMBOLS_AND_TABLES,STRATEGY_TYPES,SLEEP_DURATION ,MAX_RETRIES,RED ,GREEN,YELLOW,BLUE,RESET
# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize ClickHouse client
client = get_clickhouse_client()

async def analyze_strategy(
    df_4h: List[Dict[str, Any]], df_30m: List[Dict[str, Any]], 
    df_15m: List[Dict[str, Any]], strategy_type: List[str], symbol: str
) -> List[Dict[str, Any]]:
    """
    Generate trading signals based on the selected strategies.
    
    :param df_4h: List of dictionaries containing data for the 4-hour time frame.
    :param df_30m: List of dictionaries containing data for the 30-minute time frame.
    :param df_15m: List of dictionaries containing data for the 15-minute time frame.
    :param strategy_type: List of strategy types to use for signal generation (e.g., ["Malaysian", "Moving Average"]).
    :param symbol: The trading symbol (e.g., "frxEURUSD").
    :return: List of trading signals, where each signal is a dictionary with details like Entry, SL, TP, etc.
    """
    signals = []

    # Apply Malaysian strategy if selected
    if "Malaysian" in strategy_type:
        malaysian_signals = malaysian_strategy(df_4h, df_15m, symbol)
        logger.info(f"{GREEN}Malaysian Strategy Signals generated:{RESET}")  
        signals.extend(malaysian_signals)

    # Apply Moving Average strategy if selected
    if "Moving Average" in strategy_type:
        moving_avg_signals = moving_average_strategy(df_4h, df_30m, symbol)
        logger.info(f"Moving Average Strategy Signals: {moving_avg_signals}")
        signals.extend(moving_avg_signals)

    return signals

async def save_signals_to_clickhouse(signals: List[Dict[str, Any]]) -> bool:
    """
    Save trading signals to a ClickHouse database.
    
    :param signals: List of trading signals to save.
    :return: True if all signals were saved successfully, False otherwise.
    """
    table_name = "trading_signals"
    try:
        # Create the table if it doesn't exist
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                timestamp DateTime,
                Pair String,
                Signal String,
                Entry Float64,
                SL Float64,
                TP Float64
            ) ENGINE = MergeTree()
            ORDER BY timestamp
        """
        client.command(create_table_query)
        logger.info("Trading signals table created or verified in ClickHouse.")
        
        # Insert each signal into the table
        logger.info("Storing trading signals in ClickHouse...")
        for signal in signals:
            try:
                client.command(f"""
                    INSERT INTO {table_name} 
                    (timestamp, Pair, Signal, Entry, SL, TP)
                    VALUES (NOW(), '{signal['Pair']}', '{signal['Signal']}', {signal['Entry']}, {signal['SL']}, {signal['TP']})
                """)
                logger.info(f"Signal stored: {signal}")
                print("signal Stored :",signal)
            except Exception as e:
                logger.error(f"Failed to store signal: {signal}. Error: {e}")
                return False
        return True
    except Exception as e:
        logger.error(f"Error setting up ClickHouse table or storing signals: {e}")
        return False

async def prepare_trading(signals: List[Dict[str, Any]], strategy_type: List[str], symbol: str):
    """
    Prepare and execute trades based on generated signals.
    
    :param signals: List of trading signals.
    :param strategy_type: List of strategy types (e.g., ["Malaysian", "Moving Average"]).
    :param symbol: The trading symbol (e.g., "frxEURUSD").
    """
    try:
        logger.info("Preparing trading...")
        
        # Fetch users eligible for trading based on the strategy
        result = client.query(f"""
           SELECT token, email FROM userdetails WHERE strategy = '{strategy_type}' AND trading = 'true' AND trading_today = 'true'
        """)
        
        if not result.result_set:
            logger.warning("No active tokens found for the specified strategy.")
            return
        
        logger.info(f"Found tokens for trading: {result.result_set}")
        
        # Process each signal and execute trades for eligible users
        for signal in signals:
            for row in result.result_set:
                token, email = row[0], row[1]  # Extract token and email from the row
                logger.info(f"Processing token: {token} associated with email: {email}")
                
                # Check if the user is eligible to trade today
                eligible = await eligible_user(email, token)
                
                if eligible == 'true':
                    # Fetch symbols associated with the user's token
                    symbols_result = client.query(f"""
                        SELECT symbol FROM symbols 
                        WHERE token = '{token}'
                    """)
                    symbols = [row[0] for row in symbols_result.result_set]
                    
                    # If the symbol matches, calculate risk and execute the trade
                    if symbol in symbols:
                        risk_amount = await calculate_risk(token, signal['Entry'], signal['SL'])
                        if risk_amount > 0:
                            if signal['Signal'] == "Buy":
                                logger.info(f"Placing BUY trade for {symbol} with risk amount {risk_amount}")
                                # executeTrade(token, risk_amount, signal['TP'], signal['SL'], symbol)
                                logger.info("BUY trade executed successfully.")
                            elif signal['Signal'] == "Sell":
                                logger.info(f"Placing SELL trade for {symbol} with risk amount {risk_amount}")
                                # executeTrade(token, risk_amount, signal['TP'], signal['SL'], symbol)
                                logger.info("SELL trade executed successfully.")
                            else:
                                logger.warning("Unknown signal type encountered.")
                        else:
                            logger.warning(f"Risk amount too low for token {token}. Trade skipped.")
            
    except Exception as e:
        logger.error(f"Error in prepare_trading: {e}")

async def process_symbol(symbol: str, table_name: str) -> Optional[List[Dict[str, Any]]]:
    """
    Process a single symbol: fetch data, aggregate, analyze, and generate signals.
    
    :param symbol: The trading symbol (e.g., "frxEURUSD").
    :param table_name: The corresponding table name in the database.
    :return: List of trading signals if successful, None otherwise.
    """
    logger.info(f"Starting operations for {symbol} (Table: {table_name})...")
    
    # Align the current time to the nearest minute
    now_utc = datetime.utcnow()
    aligned_time = now_utc.replace(second=0, microsecond=0)
    aligned_time_cat = aligned_time.astimezone(CAT_TIMEZONE)
    
    # Fetch forex data for the symbol
    logger.info("Fetching forex data...")
    df_minute = fetch_forex_data(table_name)
    if df_minute is None:
        logger.error(f"Failed to fetch forex data for {symbol}. Retrying in 60 seconds...")
        await asyncio.sleep(60)
        return None
    
    logger.info("Forex data fetched successfully.")
    
    # Aggregate data into 4H, 30M, and 15M intervals
    logger.info("Aggregating data into 4H, 30M, and 15M intervals...")
    df_4h = aggregate_data(df_minute, "4H")
    df_15m = aggregate_data(df_minute, "15M")
    df_30m = aggregate_data(df_minute, "30M")
    logger.info("Data aggregation complete.")
    
    # Analyze strategy and generate trading signals
    logger.info("Analyzing trading strategy...")
    signals = await analyze_strategy(df_4h, df_30m, df_15m, STRATEGY_TYPES, symbol)
    
    if signals:
        # Save signals to ClickHouse and prepare trades
        if await save_signals_to_clickhouse(signals):
            print('Tradeing COmented wame check line  193')
            # await prepare_trading(signals, STRATEGY_TYPES, symbol)
        else:
            logger.error("Failed to save signals to ClickHouse.")
    else:
        logger.info("No trading signals generated.")
    
    return signals

async def main():
    """
    Main loop to process all symbols.
    """
    while True:
        try:
            # Process each symbol in the SYMBOLS_AND_TABLES dictionary
            for symbol, table_name in SYMBOLS_AND_TABLES.items():
                await process_symbol(symbol, table_name)
        except Exception as e:
            logger.error(f"Exception in main loop: {e}")
        
        # Sleep for the next interval (4 hours)
        logger.info(f"Sleeping for {SLEEP_DURATION // 3600} hours...\n")
        await asyncio.sleep(SLEEP_DURATION)