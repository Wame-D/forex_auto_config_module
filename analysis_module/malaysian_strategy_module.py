import logging
from datetime import timedelta
from typing import List, Dict, Any
from .risk_management import calculate_stop_loss, calculate_take_profit
from .constants import DEFAULT_BUFFER_PIPS, HIGH_RISK_RATIO, LOW_RISK_RATIO, GREEN, YELLOW, BLUE, RESET

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def has_reversal_pattern(candle: Dict[str, Any], signal_type: str) -> bool:
    """
    Check if a reversal pattern exists in the candle data.
    - For a Buy signal, the candle should close higher than it opened (bullish).
    - For a Sell signal, the candle should close lower than it opened (bearish).
    """
    try:
        if signal_type == "Buy" and candle["close"] > candle["open"]:
            return True
        elif signal_type == "Sell" and candle["close"] < candle["open"]:
            return True
    except KeyError as e:
        logger.error(f"Missing key in candle data: {e}")
    return False

def validate_small_support_resistance(
    candles_15m: List[Dict[str, Any]], signal_type: str
) -> bool:
    """
    Validate small support or resistance levels on the 15-minute chart.
    - Iterates through the 15-minute candles and checks for reversal patterns.
    - Returns True if any candle shows a valid reversal pattern for the given signal type.
    """
    for candle in candles_15m:
        if has_reversal_pattern(candle, signal_type):
            return True
    return False

def get_signal_type(
    prev_candle: Dict[str, Any], current_candle: Dict[str, Any]
) -> str:
    """
    Identify the signal type (Buy/Sell) based on the previous and current candles.
    - A Buy signal is generated if the current candle's low and close are higher than the previous candle's.
    - A Sell signal is generated if the current candle's high and close are lower than the previous candle's.
    """
    signal_type = None

    if prev_candle["low"] < current_candle["low"] and prev_candle["close"] < current_candle["close"]:
        signal_type = "Buy"
    elif prev_candle["high"] > current_candle["high"] and prev_candle["close"] > current_candle["close"]:
        signal_type = "Sell"

    return signal_type

def calculate_support_resistance(
    candles: List[Dict[str, Any]], signal_type: str
) -> float:
    """
    Calculate support or resistance levels based on the candle sequence.
    - For Buy signals, support is the low of the bearish candle.
    - For Sell signals, resistance is the high of the bullish candle.
    """
    if signal_type == "Buy":
        return min(candle["low"] for candle in candles)
    elif signal_type == "Sell":
        return max(candle["high"] for candle in candles)
    return 0.0

def adjust_sl_tp_within_15m(
    candles_15m: List[Dict[str, Any]], signal: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Adjust the Stop Loss (SL) and Take Profit (TP) based on the next 15 minutes' price action.
    - For Buy signals:
      - SL is adjusted to the lowest low in the next 15 minutes.
      - TP is adjusted to the highest high in the next 15 minutes.
    - For Sell signals:
      - SL is adjusted to the highest high in the next 15 minutes.
      - TP is adjusted to the lowest low in the next 15 minutes.
    - Recalculates TP to maintain a favorable risk-reward ratio.
    - Ensures SL and TP are rounded to 4 decimal places.
    """
    entry_price = signal["Entry"]
    signal_type = signal["Signal"]
    adjusted_sl = signal["SL"]
    adjusted_tp = signal["TP"]

    for candle in candles_15m:
        try:
            if signal_type == "Buy":
                if candle["low"] < adjusted_sl:
                    adjusted_sl = candle["low"]
                if candle["high"] > adjusted_tp:
                    adjusted_tp = candle["high"]
            elif signal_type == "Sell":
                if candle["high"] > adjusted_sl:
                    adjusted_sl = candle["high"]
                if candle["low"] < adjusted_tp:
                    adjusted_tp = candle["low"]
        except KeyError as e:
            logger.error(f"Missing key in candle data during SL/TP adjustment: {e}")

    # Recalculate TP to maintain a favorable risk-reward ratio
    if signal_type == "Buy":
        adjusted_tp = max(adjusted_tp, entry_price + (entry_price - adjusted_sl) * HIGH_RISK_RATIO)
    elif signal_type == "Sell":
        adjusted_tp = min(adjusted_tp, entry_price - (adjusted_sl - entry_price) * HIGH_RISK_RATIO)

    # Ensure SL and TP are not zero or negative
    adjusted_sl = max(adjusted_sl, 0)
    adjusted_tp = max(adjusted_tp, 0)

    # Round SL and TP to 4 decimal places to match candle prices
    adjusted_sl = round(adjusted_sl, 4)
    adjusted_tp = round(adjusted_tp, 4)

    # Update SL and TP in the signal
    signal["SL"] = adjusted_sl
    signal["TP"] = adjusted_tp
    return signal

def filter_perfect_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters signals to retain only the ones that meet all requirements and are highly profitable.
    - Requires a minimum risk-reward ratio of 2:1.
    - Skips signals with invalid SL or Entry values.
    """
    filtered_signals = []
    for signal in signals:
        try:
            risk_reward_ratio = abs((signal["TP"] - signal["Entry"]) / (signal["Entry"] - signal["SL"]))
            if risk_reward_ratio >= 2:  # Require at least a 2:1 risk-reward ratio
                filtered_signals.append(signal)
        except ZeroDivisionError:
            logger.warning(f"Skipping signal with invalid SL/Entry values: {signal}")
        except KeyError as e:
            logger.error(f"Missing key in signal data: {e}")
    logger.info(f"Filtered signals: {len(filtered_signals)} out of {len(signals)}.")
    return filtered_signals

def malaysian_strategy(
    candles_4h: List[Dict[str, Any]], candles_15m: List[Dict[str, Any]], symbol: str
) -> List[Dict[str, Any]]:
    """
    Analyzes forex data using the enhanced Malaysian Forex Trading Strategy.
    - Processes 4-hour candles to identify signals.
    - Validates signals using 15-minute candles.
    - Adjusts SL and TP based on 15-minute price action.
    - Filters signals to retain only the most profitable ones.
    - Ensures Entry, SL, and TP are rounded to 4 decimal places.
    """
    logger.info("Starting analysis for Enhanced Malaysian Forex Strategy...")
    signals = []

    try:
        for i in range(1, len(candles_4h)):
            prev_candle = candles_4h[i - 1]
            current_candle = candles_4h[i]
            entry_price = current_candle["close"]
            pair = symbol

            # Step 1: Identify the signal type (Buy/Sell)
            signal_type = get_signal_type(prev_candle, current_candle)

            if not signal_type:
                continue  # Skip if no signal is identified

            # Step 2: Calculate support/resistance levels
            support_resistance_level = calculate_support_resistance([prev_candle, current_candle], signal_type)

            # Step 3: Validate the signal on the 15-minute chart
            valid = any(
                has_reversal_pattern(candle, signal_type)
                for candle in candles_15m
                if candle["timestamp"] >= current_candle["timestamp"] - timedelta(hours=4)
            )
            if not valid:
                logger.info(f"Signal at index {i} invalidated by 15-minute chart. Skipping...")
                continue

            # Step 4: Check for small support/resistance levels on the 15-minute chart
            if not validate_small_support_resistance(candles_15m, signal_type):
                logger.info(f"No support/resistance validation for signal at index {i}. Skipping...")
                continue

            # Step 5: Calculate Stop Loss and Take Profit
            stop_loss = calculate_stop_loss(entry_price, signal_type, DEFAULT_BUFFER_PIPS)
            take_profit = calculate_take_profit(entry_price, stop_loss, signal_type, LOW_RISK_RATIO)

            # Step 6: Validate SL and TP
            if stop_loss == entry_price or take_profit == entry_price:
                logger.warning(f"Invalid SL/TP values for signal at index {i}. Skipping...")
                continue

            # Step 7: Create the initial signal
            signal = {
                "Pair": pair,
                "Signal": signal_type,
                "Entry": round(float(entry_price), 4),  # Round Entry to 4 decimal places
                "SL": round(float(stop_loss), 4),       # Round SL to 4 decimal places
                "TP": round(float(take_profit), 4),     # Round TP to 4 decimal places
            }

            # Step 8: Adjust SL and TP within the next 15 minutes
            signal = adjust_sl_tp_within_15m(candles_15m, signal)

            # Step 9: Append the adjusted signal
            signals.append(signal)

        # Step 10: Filter signals to retain only perfect ones
        perfect_signals = filter_perfect_signals(signals)

        logger.info(f"Generated {len(perfect_signals)} perfect signals.")
        return perfect_signals

    except Exception as e:
        logger.exception("Error during strategy analysis.")
        return []