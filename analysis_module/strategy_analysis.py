import logging
from datetime import timedelta
from typing import List, Dict, Any
from .risk_management import (
    calculate_stop_loss,
    calculate_take_profit,
    calculate_position_size,
)
from .constants import (
    DEFAULT_BUFFER_PIPS,
    EXOTIC_PAIRS,
    PIP_VALUE,
    HIGH_RISK_RATIO,
    LOW_RISK_RATIO,
    TIMEFRAMES,
)

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def is_price_within_safe_zone(
    candle: Dict[str, Any], signal_type: str, safe_zone_top: float, safe_zone_bottom: float
) -> bool:
    """
    Check if the price is within the defined safe zone.
    """
    if signal_type == "Buy":
        return safe_zone_bottom <= candle["low"] <= safe_zone_top  # Buy signal: low of the candle within the safe zone
    elif signal_type == "Sell":
        return safe_zone_bottom <= candle["high"] <= safe_zone_top  # Sell signal: high of the candle within the safe zone
    return False


def has_reversal_pattern(candle: Dict[str, Any], signal_type: str) -> bool:
    """
    Check if a reversal pattern (bullish for buy, bearish for sell) exists.
    """
    if signal_type == "Buy" and candle["close"] > candle["open"]:  # Bullish pattern for buy
        return True
    elif signal_type == "Sell" and candle["close"] < candle["open"]:  # Bearish pattern for sell
        return True
    return False


def validate_small_support_resistance(
    candles_15m: List[Dict[str, Any]], signal_type: str, safe_zone_top: float, safe_zone_bottom: float
) -> bool:
    """
    Validate if there are small support or resistance levels within the safe zone on the 15-minute chart.
    """
    for candle in candles_15m:
        if is_price_within_safe_zone(candle, signal_type, safe_zone_top, safe_zone_bottom) and has_reversal_pattern(candle, signal_type):
            return True
    return False


def get_signal_type_and_safe_zone(prev_candle: Dict[str, Any], current_candle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify the signal type (Buy/Sell) and calculate the safe zone based on previous and current candle.
    """
    signal_type = None
    safe_zone_top = None
    safe_zone_bottom = None

    if prev_candle["low"] < current_candle["low"] and prev_candle["close"] < current_candle["close"]:
        signal_type = "Buy"
        safe_zone_top = prev_candle["open"] + (2 * PIP_VALUE)
        safe_zone_bottom = prev_candle["open"] - (2 * PIP_VALUE)
    elif prev_candle["high"] > current_candle["high"] and prev_candle["close"] > current_candle["close"]:
        signal_type = "Sell"
        safe_zone_top = prev_candle["open"] + (2 * PIP_VALUE)
        safe_zone_bottom = prev_candle["open"] - (2 * PIP_VALUE)

    return {
        "signal_type": signal_type,
        "safe_zone_top": safe_zone_top,
        "safe_zone_bottom": safe_zone_bottom
    }

def analyze_malaysian_strategy(
    candles_4h: List[Dict[str, Any]], candles_15m: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Analyzes forex data using the Professional Malaysian Forex Trading Strategy.

    Returns:
        List[Dict[str, Any]]: A list of signals with relevant trade details.
    """
    logger.info("Starting analysis for Professional Malaysian Forex Strategy...")
    signals = []

    try:
        for i in range(1, len(candles_4h)):
            prev_candle = candles_4h[i - 1]
            current_candle = candles_4h[i]
            entry_price = current_candle["close"]
            pair = current_candle.get("pair", "frxEURUSD")

            # Skip exotic pairs
            if pair in EXOTIC_PAIRS:
                logger.warning(f"Skipping exotic pair: {pair}")
                continue

            # Get signal type and safe zone
            signal_data = get_signal_type_and_safe_zone(prev_candle, current_candle)
            signal_type = signal_data.get("signal_type")
            safe_zone_top = signal_data.get("safe_zone_top")
            safe_zone_bottom = signal_data.get("safe_zone_bottom")

            if not signal_type:
                continue

            # Validate on 15-minute chart
            valid = any(
                is_price_within_safe_zone(candle, signal_type, safe_zone_top, safe_zone_bottom)
                for candle in candles_15m
                if candle["timestamp"] >= current_candle["timestamp"] - timedelta(hours=4)
            )
            if not valid:
                logger.info(f"Signal at index {i} invalidated by 15-minute chart. Skipping...")
                continue

            # Check support/resistance on 15-minute chart
            if not validate_small_support_resistance(candles_15m, signal_type, safe_zone_top, safe_zone_bottom):
                logger.info(f"No support/resistance validation for signal at index {i}. Skipping...")
                continue

            # Calculate Stop Loss and Take Profit
            stop_loss = calculate_stop_loss(entry_price, signal_type, DEFAULT_BUFFER_PIPS)
            take_profit = calculate_take_profit(entry_price, stop_loss, signal_type, LOW_RISK_RATIO)

            if stop_loss == entry_price or take_profit == entry_price:
                logger.warning(f"Invalid SL/TP values for signal at index {i}. Skipping...")
                continue

            # Append the signal
            signals.append({
                "Pair": pair,
                "Signal": signal_type,
                "Entry": round(entry_price, 2),
                "SL": round(stop_loss, 2),
                "TP": round(take_profit, 2),
                "Risk Amount": 1,  # Placeholder
                "Position Size": 1,  # Placeholder
                "Safe Zone Top": round(safe_zone_top, 5),
                "Safe Zone Bottom": round(safe_zone_bottom, 5),
            })

        logger.info(f"Generated {len(signals)} signals.")
    
        return signals

    except Exception as e:
        logger.exception("Error during strategy analysis.")
        return []
