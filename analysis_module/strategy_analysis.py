import logging
from datetime import timedelta
from typing import List, Dict, Any
from .risk_management import calculate_stop_loss, calculate_take_profit
from .constants import DEFAULT_BUFFER_PIPS, EXOTIC_PAIRS, PIP_VALUE, HIGH_RISK_RATIO, LOW_RISK_RATIO
from .strategy import  moving_average_strategy
# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
GREEN = '\033[92m'
RESET = '\033[0m'  


def is_price_within_safe_zone(
    candle: Dict[str, Any], signal_type: str, safe_zone_top: float, safe_zone_bottom: float
) -> bool:
    """Check if the price is within the defined safe zone."""
    try:
        if signal_type == "Buy":
            return safe_zone_bottom <= candle["low"] <= safe_zone_top
        elif signal_type == "Sell":
            return safe_zone_bottom <= candle["high"] <= safe_zone_top
    except KeyError as e:
        logger.error(f"Missing key in candle data: {e}")
    return False

def has_reversal_pattern(candle: Dict[str, Any], signal_type: str) -> bool:
    """Check if a reversal pattern exists (bullish for Buy, bearish for Sell)."""
    try:
        if signal_type == "Buy" and candle["close"] > candle["open"]:
            return True
        elif signal_type == "Sell" and candle["close"] < candle["open"]:
            return True
    except KeyError as e:
        logger.error(f"Missing key in candle data: {e}")
    return False

def validate_small_support_resistance(
    candles_15m: List[Dict[str, Any]], signal_type: str, safe_zone_top: float, safe_zone_bottom: float
) -> bool:
    """Validate small support or resistance levels within the safe zone on the 15-minute chart."""
    for candle in candles_15m:
        if is_price_within_safe_zone(candle, signal_type, safe_zone_top, safe_zone_bottom) and has_reversal_pattern(candle, signal_type):
            return True
    return False

def get_signal_type_and_safe_zone(
    prev_candle: Dict[str, Any], current_candle: Dict[str, Any]
) -> Dict[str, Any]:
    """Identify the signal type (Buy/Sell) and calculate the safe zone based on the previous and current candles."""
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
        "safe_zone_bottom": safe_zone_bottom,
    }

def adjust_sl_tp_within_15m(
    candles_15m: List[Dict[str, Any]], signal: Dict[str, Any]
) -> Dict[str, Any]:
    """Adjust the Stop Loss (SL) and Take Profit (TP) based on the next 15 minutes' price action."""
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

    signal["SL"] = round(adjusted_sl, 2)
    signal["TP"] = round(adjusted_tp, 2)
    return signal

def filter_perfect_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filters signals to retain only the ones that meet all requirements and are highly profitable."""
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
    # logger.info(f"Filtered signals: {len(filtered_signals)} out of {len(signals)}.")
    return filtered_signals

def analyze_malaysian_strategy(
    candles_4h: List[Dict[str, Any]], candles_15m: List[Dict[str, Any]], symbol
) -> List[Dict[str, Any]]:
    """Analyzes forex data using the enhanced Malaysian Forex Trading Strategy."""
    # logger.info("Starting analysis for Enhanced Malaysian Forex Strategy...")
    signals = []

    try:
        for i in range(1, len(candles_4h)):
            prev_candle = candles_4h[i - 1]
            current_candle = candles_4h[i]
            entry_price = current_candle["close"]
            pair = symbol

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

            # Validate SL and TP
            if stop_loss == entry_price or take_profit == entry_price:
                logger.warning(f"Invalid SL/TP values for signal at index {i}. Skipping...")
                continue

            # Create the initial signal
            signal = {
                "Pair": pair,
                "Signal": signal_type,
                "Entry": round(entry_price, 2),
                "SL": round(stop_loss, 2),
                "TP": round(take_profit, 2),
                "Safe Zone Top": round(safe_zone_top, 5),
                "Safe Zone Bottom": round(safe_zone_bottom, 5),
            }

            # Adjust SL and TP within the next 15 minutes
            signal = adjust_sl_tp_within_15m(candles_15m, signal)

            # Append the adjusted signal
            signals.append(signal)

        # Filter signals to retain only perfect ones
        perfect_signals = filter_perfect_signals(signals)

        # logger.info(f"Generated {len(perfect_signals)} perfect signals.")
        return perfect_signals

    except Exception as e:
        logger.exception("Error during strategy analysis.")
        return []
def analysis(
    df_4h: List[Dict[str, Any]], df_30m: List[Dict[str, Any]], 
    df_15m: List[Dict[str, Any]], strategy_type: List[str], symbol
) -> List[Dict[str, Any]]:
    """
    Generate trading signals based on the selected strategies.
    
    :param df_4h: List of dicts containing data for the 4-hour time frame.
    :param df_30m: List of dicts containing data for the 30-minute time frame.
    :param df_15m: List of dicts containing data for the 15-minute time frame.
    :param strategy_type: List of strategy types to use for signal generation (e.g., ["Malaysian", "Moving Average"]).
    :return: List of trading signals based on the selected strategies.
    """
    signals = []

    if "Malaysian" in strategy_type:
        malaysian_signals = analyze_malaysian_strategy(df_4h, df_15m, symbol)
        # print(f"{GREEN }Malaysian Strategy Signals generet:{RESET}")  
        signals.extend(malaysian_signals)

    if "Moving Average" in strategy_type:
        moving_avg_signals = moving_average_strategy(df_4h, df_30m)
        # ("Moving Average Strategy Signals:", moving_avg_signals)  # Debugging statement
        signals.extend(moving_avg_signals)

    return signals
