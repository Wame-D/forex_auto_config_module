import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from bot_settings.views import get_candles

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Constants for the Forex Strategy
PIP_VALUE = 0.0001
ACCOUNT_BALANCE = 100
RISK_PERCENTAGE = 2
REWARD_TO_RISK_RATIO = 2  # Default reward-to-risk ratio
TIMEFRAMES = {"4H": 240, "15M": 15}  # Timeframe in minutes


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


def fetch_forex_data(request) -> Optional[List[Dict[str, Any]]]:
    """
    Fetches real-time forex data (minute-level candles) and returns parsed data as a list of dictionaries.
    """
    logger.info("Fetching forex data...")
    try:
        response = get_candles(request)
        logger.debug(f"Raw response from get_candles: {response}")

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


def analyze_malaysian_strategy(candles_4h: List[Dict[str, Any]], candles_15m: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyzes forex data using the Malaysian Forex Strategy.
    Identifies buy and sell signals and calculates stop loss, take profit, and lot size.
    Returns a list of trading signals.
    """
    logger.info("Analyzing Malaysian Forex Strategy...")
    signals = []
    try:
        for i in range(1, len(candles_4h)):
            prev_candle = candles_4h[i - 1]
            current_candle = candles_4h[i]

            signal_type = None
            entry_price = None

            if current_candle["close"] > prev_candle["high"]:  # Breakout condition
                signal_type = "Buy"
                entry_price = current_candle["close"]
            elif current_candle["close"] < prev_candle["low"]:  # Breakdown condition
                signal_type = "Sell"
                entry_price = current_candle["close"]

            if signal_type:
                start_time = current_candle["timestamp"]
                end_time = start_time + timedelta(hours=4)
                segment = [c for c in candles_15m if start_time <= c["timestamp"] < end_time]

                confirmation = any(
                    (signal_type == "Buy" and c["close"] > c["open"]) or
                    (signal_type == "Sell" and c["close"] < c["open"]) for c in segment
                )

                if confirmation:
                    risk_amount = ACCOUNT_BALANCE * (RISK_PERCENTAGE / 100)
                    stop_loss = (
                        entry_price - (prev_candle["high"] - prev_candle["low"]) * PIP_VALUE
                        if signal_type == "Buy"
                        else entry_price + (prev_candle["high"] - prev_candle["low"]) * PIP_VALUE
                    )
                    take_profit = (
                        entry_price + REWARD_TO_RISK_RATIO * (entry_price - stop_loss)
                        if signal_type == "Buy"
                        else entry_price - REWARD_TO_RISK_RATIO * (stop_loss - entry_price)
                    )

                    position_size = risk_amount / abs(entry_price - stop_loss)
                    signals.append({
                        "Signal": signal_type,
                        "Entry": round(entry_price, 5),
                        "SL": round(stop_loss, 5),
                        "TP": round(take_profit, 5),
                        "Lot Size": round(position_size, 2),
                    })

        logger.info(f"Generated {len(signals)} signals.")
        return signals
    except Exception as e:
        logger.exception(f"Error analyzing strategy: {e}")
        return []
