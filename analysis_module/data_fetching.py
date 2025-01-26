import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from forex.clickhouse.connection import get_clickhouse_client

# Initialize ClickHouse client
client = get_clickhouse_client()
# from bot_settings.views import get_candles

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def parse_forex_data(candles: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """
    Validates and parses candle data.
    """
    logger.info("Parsing candle data...")
    required_keys = {"timestamp", "open", "high", "low", "close"}
    parsed_candles = []

    for candle in candles:
        if not required_keys.issubset(candle.keys()):
            logger.error(f"Missing required keys in candle: {candle}")
            return None
        try:
            parsed_candles.append({
                "timestamp": datetime.fromisoformat(candle["timestamp"]),
                "open": float(candle["open"]),
                "high": float(candle["high"]),
                "low": float(candle["low"]),
                "close": float(candle["close"]),
            })
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid data format in candle: {candle}, Error: {e}")
            return None

    logger.info(f"Successfully parsed {len(parsed_candles)} candles.")
    return parsed_candles


def fetch_forex_data() -> Optional[List[Dict[str, Any]]]:
    """
    Fetches real-time forex data (minute-level candles) and returns parsed data as a list of dictionaries.
    """
    logger.info("Fetching forex data...")
    try:
        response = get_candles()
        if isinstance(response, dict) and "error" in response:
            logger.error(f"Error fetching forex data: {response['error']}")
            return None

        candles = response if isinstance(response, list) else response.get("candles", [])
        if not candles:
            logger.error("No valid candles data received or incorrect format.")
            return None

        return parse_forex_data(candles)
    except Exception as e:
        logger.exception(f"Error fetching forex data: {e}")
        return None
    
# fETCHING eURO/USD candles  
def get_candles():
    try:
        #valid_tables = ['eurousd', 'v75_candles', 'us30_candles']
        # Execute the query to fetch candle data
        table_name = "eurousd" 
        result = client.query(f"""
            SELECT * 
            FROM {table_name} 
            WHERE timestamp >= now() - INTERVAL 360 HOUR 
            ORDER BY timestamp
        """)

        # Parse the result into a structured response
        candles = [
            {
                "timestamp": row[result.column_names.index("timestamp")].isoformat(),
                "open": round(row[result.column_names.index("open")], 4),
                "high": round(row[result.column_names.index("high")], 4),
                "low": round(row[result.column_names.index("low")], 4),
                "close": round(row[result.column_names.index("close")], 4),
            }
            for row in result.result_set
        ]

        return candles

    except Exception as e:
        return ({"error": str(e)})

