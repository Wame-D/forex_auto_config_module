from datetime import datetime, timedelta
from typing import List

PIP_VALUE = 0.0001  # Adjust as needed for your Forex pairs

def aggregate_candles(candles: List[dict], interval_minutes: int) -> List[dict]:
    """Aggregate candles into specified time intervals."""
    aggregated = []
    interval_delta = timedelta(minutes=interval_minutes)
    start_time = None
    open_price = high_price = low_price = close_price = None

    for candle in candles:
        current_time = datetime.fromisoformat(candle["timestamp"])
        if start_time is None or current_time >= start_time + interval_delta:
            if start_time is not None:  # Save the previous interval's candle
                aggregated.append({
                    "timestamp": start_time.isoformat(),
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                })
            start_time = current_time.replace(
                minute=(current_time.minute // interval_minutes) * interval_minutes, 
                second=0, microsecond=0
            )
            open_price = candle["open"]
            high_price = candle["high"]
            low_price = candle["low"]
            close_price = candle["close"]
        else:
            high_price = max(high_price, candle["high"])
            low_price = min(low_price, candle["low"])
            close_price = candle["close"]

    if start_time is not None:
        aggregated.append({
            "timestamp": start_time.isoformat(),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
        })
    return aggregated


def find_key_patterns(data: List[dict]):
    """Find candlestick patterns such as support and resistance."""
    key_patterns = []
    for i in range(1, len(data)):
        current = data[i]
        previous = data[i - 1]
        if previous['close'] > previous['open'] and current['close'] < current['open']:
            key_patterns.append({"pattern": "support", "timestamp": current["timestamp"], "candle": current})
        elif previous['close'] < previous['open'] and current['close'] > current['open']:
            key_patterns.append({"pattern": "resistance", "timestamp": current["timestamp"], "candle": current})
    return key_patterns


def confirm_pattern(data: List[dict], pattern: dict) -> bool:
    """Confirm the presence of a candlestick pattern."""
    pattern_time = datetime.fromisoformat(pattern["timestamp"])
    confirmation_candles = [
        candle for candle in data if datetime.fromisoformat(candle["timestamp"]) >= pattern_time
    ]
    for candle in confirmation_candles:
        if pattern["pattern"] == "support" and candle["close"] > candle["open"]:
            return True
        elif pattern["pattern"] == "resistance" and candle["close"] < candle["open"]:
            return True
    return False


def generate_signals(candles_4h, candles_15m, moving_averages, atr_period, strategy_choice="both"):
    """Generate trading signals based on strategies."""
    signals = []
    if strategy_choice in ["malaysian", "both"]:
        key_patterns = find_key_patterns(candles_4h)
        for pattern in key_patterns:
            if confirm_pattern(candles_15m, pattern):
                safe_zone = calculate_safe_zone(pattern["candle"], pattern["pattern"])
                signals.append({"timestamp": pattern["timestamp"], "type": pattern["pattern"], **safe_zone})
    
    if strategy_choice in ["moving_average", "both"]:
        ma_signals = find_moving_average_signals(candles_15m, moving_averages, atr_period)
        signals.extend(ma_signals)
    
    return signals


def calculate_moving_average(candles, period):
    """Calculate moving averages for a given period."""
    ma_values = []
    for i in range(len(candles)):
        if i < period - 1:
            ma_values.append(None)
        else:
            ma_values.append(sum(c["close"] for c in candles[i - period + 1:i + 1]) / period)
    return ma_values


def find_moving_average_signals(candles, moving_averages, atr_period):
    """Generate signals based on moving averages."""
    ma = {period: calculate_moving_average(candles, period) for period in moving_averages}
    signals = []
    for i in range(max(moving_averages), len(candles)):
        atr = calculate_atr(candles, atr_period)  # Assuming calculate_atr is defined elsewhere
        if ma[7][i] > ma[14][i] and ma[89][i] > ma[200][i]:
            signals.append({"timestamp": candles[i]["timestamp"], "type": "BUY", "atr": atr, "entry": candles[i]["close"]})
        elif ma[7][i] < ma[14][i] and ma[89][i] < ma[200][i]:
            signals.append({"timestamp": candles[i]["timestamp"], "type": "SELL", "atr": atr, "entry": candles[i]["close"]})
    return signals
