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
        # Determine the number of minutes for the selected timeframe
        timeframe_minutes = TIMEFRAMES[timeframe]
        aggregated = []
        current_candle = None

        for candle in candles:
            # Extract the timestamp from the candle
            timestamp = candle["timestamp"]
            # Adjust the timestamp to the start of the current timeframe period
            period_start = timestamp - timedelta(minutes=timestamp.minute % timeframe_minutes,
                                                 seconds=timestamp.second, microseconds=timestamp.microsecond)

            # Check if the current candle is for a new period, otherwise update the existing one
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
                # Update the high, low, and close for the ongoing candle
                current_candle["high"] = max(current_candle["high"], candle["high"])
                current_candle["low"] = min(current_candle["low"], candle["low"])
                current_candle["close"] = candle["close"]

        # Append the last candle
        if current_candle:
            aggregated.append(current_candle)

        logger.info(f"Successfully aggregated {len(aggregated)} candles for {timeframe}.")
        return aggregated
    except Exception as e:
        logger.exception(f"Error aggregating data: {e}")
        return []