from datetime import timedelta
from typing import List, Dict, Any
from .risk_management import calculate_stop_loss, calculate_take_profit, calculate_position_size
from .constants import EXOTIC_PAIRS, ATR_PERIOD, RSI_PERIOD, ADX_THRESHOLD, PIP_VALUE, HIGH_RISK_RATIO, LOW_RISK_RATIO

# Print statements for logging and debugging
def print_debug(message: str):
    print(f"[DEBUG] {message}")

def print_info(message: str):
    print(f"[INFO] {message}")

def print_warning(message: str):
    print(f"[WARNING] {message}")

def print_error(message: str):
    print(f"[ERROR] {message}")

def calculate_atr(candles: List[Dict[str, Any]], period: int) -> float:
    """Calculate the Average True Range (ATR) for volatility-based risk management."""
    # print_info("Calculating ATR...")
    tr_values = []
    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i - 1]["close"]
        tr_values.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    
    atr_value = sum(tr_values[-period:]) / period
    # print_debug(f"Calculated ATR: {atr_value}")
    return atr_value

def calculate_adx(candles: List[Dict[str, Any]], period: int) -> float:
    """Calculate the Average Directional Index (ADX) to measure trend strength."""
    try:
        # print_info("Calculating ADX...")
        # Calculate directional movements (DM+ and DM-)
        dm_plus = [candles[i]["high"] - candles[i-1]["high"] for i in range(1, len(candles))]
        dm_minus = [candles[i-1]["low"] - candles[i]["low"] for i in range(1, len(candles))]

        # True Range (TR)
        tr = [max(candles[i]["high"] - candles[i]["low"],
                  abs(candles[i]["high"] - candles[i-1]["close"]),
                  abs(candles[i]["low"] - candles[i-1]["close"])) for i in range(1, len(candles))]

        # Smooth the values using the given period
        smoothed_dm_plus = sum(dm_plus[-period:]) / period
        smoothed_dm_minus = sum(dm_minus[-period:]) / period
        smoothed_tr = sum(tr[-period:]) / period

        # Calculate ADX as the difference of the smoothed DMs divided by the TR
        adx = 100 * abs(smoothed_dm_plus - smoothed_dm_minus) / smoothed_tr
        # print_debug(f"Calculated ADX: {adx}")
        return adx if adx is not None else 0  # Ensure ADX is not None
    except Exception as e:
        # print_warning(f"Error calculating ADX: {e}")
        return 0  # Return 0 in case of error or invalid ADX calculation

def calculate_rsi(candles: List[Dict[str, Any]], period: int) -> float:
    """Calculate the Relative Strength Index (RSI) for momentum filtering."""
    # print_info("Calculating RSI...")
    gains = []
    losses = []
    for i in range(1, len(candles)):
        change = candles[i]["close"] - candles[i - 1]["close"]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    # print_debug(f"Calculated RSI: {rsi}")
    return rsi

def is_valid_signal(candle: Dict[str, Any], signal_type: str, safe_zone_top: float, safe_zone_bottom: float, atr: float) -> bool:
    """Check if the signal respects the safe zone and volatility."""
    if signal_type == "Buy":
        valid = candle["low"] >= safe_zone_bottom and candle["high"] <= safe_zone_top
        # if valid:
        #     # print_debug(f"Buy signal is valid within the safe zone.")
        # else:
            # print_debug(f"Buy signal is invalid: outside safe zone.")
        return valid
    elif signal_type == "Sell":
        # valid = candle["high"] <= safe_zone_top and candle["low"] >= safe_zone_bottom
        # if valid:
        #     # print_debug(f"Sell signal is valid within the safe zone.")
        # else:
            # print_debug(f"Sell signal is invalid: outside safe zone.")
        return valid
    return False

def calculate_safe_zone(candle: Dict[str, Any], signal_type: str, atr: float) -> Dict[str, Any]:
    """Calculate the safe zone for entry based on ATR."""
    # print_info(f"Calculating safe zone for {signal_type} signal...")
    if signal_type == "Buy":
        support_level = candle["low"]
        safe_zone_top = support_level + (atr * 0.5)
        safe_zone_bottom = support_level - (atr * 0.5)
    elif signal_type == "Sell":
        resistance_level = candle["high"]
        safe_zone_top = resistance_level + (atr * 0.5)
        safe_zone_bottom = resistance_level - (atr * 0.5)
    
    # print_debug(f"Calculated Safe Zone: Top = {safe_zone_top}, Bottom = {safe_zone_bottom}")
    return {"safe_zone_top": safe_zone_top, "safe_zone_bottom": safe_zone_bottom}

def check_candlestick_pattern(candle: Dict[str, Any], prev_candle: Dict[str, Any]) -> str:
    """Check for candlestick patterns (e.g., engulfing, pin bar)."""
    # Engulfing pattern
    if candle["close"] > candle["open"] and prev_candle["open"] > prev_candle["close"]:
        if candle["open"] < prev_candle["close"] and candle["close"] > prev_candle["open"]:
            # print_debug("Bullish Engulfing Pattern detected.")
            return "Bullish Engulfing"
    elif candle["close"] < candle["open"] and prev_candle["open"] < prev_candle["close"]:
        if candle["open"] > prev_candle["close"] and candle["close"] < prev_candle["open"]:
            # print_debug("Bearish Engulfing Pattern detected.")
            return "Bearish Engulfing"

    # Pin Bar pattern (for simplicity, considering long lower shadow)
    if candle["close"] > candle["open"] and (candle["low"] - candle["open"]) > (candle["high"] - candle["close"]):
        # print_debug("Bullish Pin Bar Pattern detected.")
        return "Bullish Pin Bar"
    elif candle["close"] < candle["open"] and (candle["high"] - candle["open"]) > (candle["low"] - candle["close"]):
        # print_debug("Bearish Pin Bar Pattern detected.")
        return "Bearish Pin Bar"
    
    return "No Pattern"

def moving_average_strategy(candles_4h: List[Dict[str, Any]], candles_30m: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Implements the moving_average_strategy based on trend, volatility, and momentum principles."""
    # print_info("Starting moving_average_strategy...")
    signals = []

    try:
        for i in range(1, len(candles_4h)):
            prev_candle = candles_4h[i - 1]
            current_candle = candles_4h[i]
            entry_price = current_candle["close"]
            pair = current_candle.get("pair", "frxEURUSD")

            # print_debug(f"Analyzing candle at index {i} for pair {pair}.")

            # Skip exotic pairs
            if pair in EXOTIC_PAIRS:
                # print_warning(f"Skipping exotic pair: {pair}")
                continue

            # Calculate Moving Averages (7, 14, 89, and 200 periods)
            short_ma = sum([candle["close"] for candle in candles_4h[max(0, i-7):i]]) / 7
            mid_ma = sum([candle["close"] for candle in candles_4h[max(0, i-14):i]]) / 14
            long_ma = sum([candle["close"] for candle in candles_4h[max(0, i-89):i]]) / 89
            long_term_ma = sum([candle["close"] for candle in candles_4h[max(0, i-200):i]]) / 200

            # Check for trend alignment (Moving Averages)
            if short_ma > mid_ma and mid_ma > long_ma and long_ma > long_term_ma:
                signal_type = "Buy"
                # print_debug(f"Signal for {pair}: Buy signal identified based on moving averages.")
            elif short_ma < mid_ma and mid_ma < long_ma and long_ma < long_term_ma:
                signal_type = "Sell"
                # print_debug(f"Signal for {pair}: Sell signal identified based on moving averages.")
            else:
                continue  # No alignment, skip this candle

            # Calculate ATR and check ADX for trend strength
            atr = calculate_atr(candles_4h, ATR_PERIOD)
            adx = calculate_adx(candles_4h, ATR_PERIOD)
            rsi = calculate_rsi(candles_30m, RSI_PERIOD)

            # print_debug(f"ADX: {adx}, ATR: {atr}, RSI: {rsi}")

            # Skip trades in choppy markets (ADX < 20)
            if adx < ADX_THRESHOLD:
                # print_info(f"Skipping signal at index {i} due to weak trend (ADX < {ADX_THRESHOLD}).")
                continue

            # Validate Safe Zone
            safe_zone_data = calculate_safe_zone(current_candle, signal_type, atr)
            safe_zone_top = safe_zone_data["safe_zone_top"]
            safe_zone_bottom = safe_zone_data["safe_zone_bottom"]

            # Validate price action on 30-minute chart
            valid = any(
                is_valid_signal(candle, signal_type, safe_zone_top, safe_zone_bottom, atr)
                for candle in candles_30m
                if candle["timestamp"] >= current_candle["timestamp"] - timedelta(hours=2)
            )
            if not valid:
                # print_info(f"Signal at index {i} invalidated by 30-minute chart. Skipping...")
                continue

            # Check for candlestick pattern confirmation
            pattern = check_candlestick_pattern(current_candle, prev_candle)
            if pattern == "No Pattern":
                # print_info(f"Signal at index {i} invalidated by lack of candlestick pattern. Skipping...")
                continue

            # Check RSI for overbought/oversold conditions
            if (signal_type == "Buy" and rsi < 50) or (signal_type == "Sell" and rsi > 50):
                # print_info(f"Signal at index {i} invalidated by RSI conditions. Skipping...")
                continue

            # Calculate Stop Loss and Take Profit based on ATR
            stop_loss = calculate_stop_loss(entry_price, signal_type, atr * 1.5)
            take_profit = calculate_take_profit(entry_price, stop_loss, signal_type, HIGH_RISK_RATIO)

            # Ensure SL and TP are not equal to entry price
            if stop_loss == entry_price or take_profit == entry_price:
                # print_warning(f"Invalid SL/TP values for signal at index {i}. Skipping...")
                continue

            # Calculate dynamic position size based on risk management
            position_size = calculate_position_size(stop_loss, PIP_VALUE)

            # Create the initial signal with calculated SL, TP, and position size
            signal = {
                "Pair": pair,
                "Signal": signal_type,
                "Entry Price": entry_price,
                "Stop Loss": stop_loss,
                "Take Profit": take_profit,
                "Position Size": position_size,
                "Pattern": pattern
            }
            signals.append(signal)

            # print_info(f"Generated trading signal for {pair} at index {i}: {signal}")

        return signals

    except Exception as e:
        print_error(f"Error in strategy execution: {e}")
        return []