import logging
from typing import List, Dict, Any
from datetime import timedelta
from .constants import TIMEFRAMES

# Set up logger for tracking the aggregation process
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def aggregate_data(candles: List[Dict[str, Any]], timeframe: str) -> List[Dict[str, Any]]:
    """
    Aggregates minute-level data into the specified timeframe.
    Returns aggregated candles for the requested timeframe.
    """
    logger.info(f"Aggregating data for {timeframe} timeframe...")

    try:
        # Determine the number of minutes for the selected timeframe from the TIMEFRAMES constant
        timeframe_minutes = TIMEFRAMES[timeframe]
        aggregated = []  # List to store the aggregated candles
        current_candle = None  # This will hold the current candle being aggregated

        # Loop through all 1-minute candles
        for candle in candles:
            # Extract the timestamp from the current 1-minute candle
            timestamp = candle["timestamp"]
            # Adjust the timestamp to the start of the current timeframe period (aligned to the timeframe)
            period_start = timestamp - timedelta(minutes=timestamp.minute % timeframe_minutes,
                                                 seconds=timestamp.second, microseconds=timestamp.microsecond)

            # If the current candle does not match the period start, it's a new timeframe period
            if not current_candle or current_candle["timestamp"] != period_start:
                # If a current candle exists, finalize and add it to the aggregated list
                if current_candle:
                    aggregated.append(current_candle)
                # Start a new aggregated candle for the new period
                current_candle = {
                    "timestamp": period_start,
                    "open": candle["open"],
                    "high": candle["high"],
                    "low": candle["low"],
                    "close": candle["close"],
                }
            else:
                # Update the existing aggregated candle with the current 1-minute candle data
                current_candle["high"] = max(current_candle["high"], candle["high"])
                current_candle["low"] = min(current_candle["low"], candle["low"])
                current_candle["close"] = candle["close"]

        # Append the last aggregated candle to the list
        if current_candle:
            aggregated.append(current_candle)

        logger.info(f"Successfully aggregated {len(aggregated)} candles for {timeframe}.")
        return aggregated

    except Exception as e:
        # Log any exceptions that occur during the aggregation process
        logger.exception(f"Error aggregating data: {e}")
        return []

def handle_missing_data(candles: List[Dict[str, Any]], timeframe: str) -> List[Dict[str, Any]]:
    """
    Handles missing data by either skipping missing candles or using interpolation to fill in the gaps.
    In this placeholder function, no interpolation is applied, but could be expanded.
    """
    logger.info("Checking for missing data...")

    # A more sophisticated interpolation strategy could be added here, but currently, we just return the original candles.
    return candles

def synchronize_timeframes(candles: List[Dict[str, Any]], timeframe: str) -> List[Dict[str, Any]]:
    """
    Ensures the candles are synchronized with the correct time.
    This method adjusts the timestamps so each candle aligns to the start of the respective timeframe.
    """
    logger.info("Synchronizing candle timestamps...")
    try:
        # Retrieve the number of minutes per timeframe
        timeframe_minutes = TIMEFRAMES[timeframe]
        for candle in candles:
            # Extract timestamp and adjust it to align with the start of the period
            timestamp = candle["timestamp"]
            period_start = timestamp - timedelta(minutes=timestamp.minute % timeframe_minutes,
                                                 seconds=timestamp.second, microseconds=timestamp.microsecond)
            # Update the candle timestamp to the period start
            candle["timestamp"] = period_start
        return candles
    except Exception as e:
        # Log any exceptions related to synchronization
        logger.exception(f"Error synchronizing timeframes: {e}")
        return []

def aggregate_and_synchronize_data(candles: List[Dict[str, Any]], timeframe: str) -> List[Dict[str, Any]]:
    """
    Main function to aggregate and synchronize data for the given timeframe.
    It ensures candles are synchronized, missing data is handled, and then performs aggregation.
    """
    # First handle missing data and synchronize timestamps
    candles = handle_missing_data(candles, timeframe)
    candles = synchronize_timeframes(candles, timeframe)

    # Then aggregate the synchronized data
    aggregated_candles = aggregate_data(candles, timeframe)

    return aggregated_candles
