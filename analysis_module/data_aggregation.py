import logging
from typing import List, Dict, Any
from datetime import timedelta
from .constants import TIMEFRAMES

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def aggregate_data(candles: List[Dict[str, Any]], timeframe: str) -> List[Dict[str, Any]]:
    """
    Aggregates minute-level data into the specified timeframe.
    Returns aggregated candles.
    """
    logger.info(f"Aggregating data for {timeframe} timeframe...")
    try:
        timeframe_minutes = TIMEFRAMES[timeframe]
        aggregated = []
        current_candle = None

        for candle in candles:
            timestamp = candle["timestamp"]
            period_start = timestamp - timedelta(minutes=timestamp.minute % timeframe_minutes,
                                                 seconds=timestamp.second, microseconds=timestamp.microsecond)

            if not current_candle or current_candle["timestamp"] != period_start:
                if current_candle:
                    aggregated.append(current_candle)
                current_candle = {
                    "timestamp": period_start,
                    "open": candle["open"],
                    "high": candle["high"],
                    "low": candle["low"],
                    "close": candle["close"],
                }
            else:
                current_candle["high"] = max(current_candle["high"], candle["high"])
                current_candle["low"] = min(current_candle["low"], candle["low"])
                current_candle["close"] = candle["close"]

        if current_candle:
            aggregated.append(current_candle)

        logger.info(f"Successfully aggregated {len(aggregated)} candles.")
        return aggregated
    except Exception as e:
        logger.exception(f"Error aggregating data: {e}")
        return []
