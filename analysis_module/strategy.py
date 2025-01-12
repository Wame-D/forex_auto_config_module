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
    
    if not aggregated:
        print("[ERROR] No candles aggregated.")
    else:
        print(f"[DEBUG] Aggregated candles into {len(aggregated)} intervals.")
        
    return aggregated

def calculate_moving_average(candles, period):
    """Calculate moving averages for a given period."""
    ma_values = []
    for i in range(len(candles)):
        if i < period - 1:
            ma_values.append(None)
        else:
            ma_values.append(sum(c["close"] for c in candles[i - period + 1:i + 1]) / period)
    return ma_values

def find_moving_average_signals(candles, moving_averages):
    """Generate signals based on moving averages."""
    ma = {period: calculate_moving_average(candles, period) for period in moving_averages}
    signals = []

    # Start checking from the max period to avoid index errors
    for i in range(max(moving_averages), len(candles)):
        # Generate BUY signal if 7-period MA > 14-period MA and 89-period MA > 200-period MA
        if ma[7][i] > ma[14][i] and ma[89][i] > ma[200][i]:
            signals.append({
                "timestamp": candles[i]["timestamp"], 
                "type": "BUY", 
                "entry": candles[i]["close"]
            })
        # Generate SELL signal if 7-period MA < 14-period MA and 89-period MA < 200-period MA
        elif ma[7][i] < ma[14][i] and ma[89][i] < ma[200][i]:
            signals.append({
                "timestamp": candles[i]["timestamp"], 
                "type": "SELL", 
                "entry": candles[i]["close"]
            })
    
    if not signals:
        print("[ERROR] No signals generated.")
    
    return signals

def generate_signals(candles_15m, moving_averages):
    """Generate trading signals based purely on the moving average strategy."""
    ma_signals = find_moving_average_signals(candles_15m, moving_averages)
    return ma_signals
