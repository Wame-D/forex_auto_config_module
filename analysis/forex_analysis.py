from datetime import datetime, timedelta
from .strategy import aggregate_candles, generate_signals
from .risk_management import calculate_position_size, calculate_trade_levels, apply_trailing_stop
from .forex_data import generate_predefined_data

PIP_VALUE = 0.0001
ACCOUNT_BALANCE = 10000
RISK_PERCENTAGE = 2
MOVING_AVERAGES = [7, 14, 89, 200]
ATR_PERIOD = 14
TIMEFRAMES = {"4H": 240, "15M": 15}

async def fetch_forex_data():
    """Fetch forex data using forex_data from the forex_data module."""
    data = generate_predefined_data()
    if not data:
        print("[ERROR] No data fetched.")
    return data

def aggregate_candles(candles, interval_minutes):
    """Aggregate candles into specified time intervals."""
    aggregated = []
    interval_delta = timedelta(minutes=interval_minutes)
    start_time = None
    open_price = high_price = low_price = close_price = None

    for candle in candles:
        current_time = datetime.fromisoformat(candle["timestamp"])
        if start_time is None or current_time >= start_time + interval_delta:
            if start_time is not None:
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
    return aggregated

async def fetch_and_analyze_forex_data():
    raw_data = await fetch_forex_data()
    if not raw_data:
        print("[ERROR] No data available for the given time range.")
        return []

    # Aggregate candles into different timeframes
    candles_4h = aggregate_candles(raw_data, TIMEFRAMES["4H"])
    candles_15m = aggregate_candles(raw_data, TIMEFRAMES["15M"])

    # Debugging logs
    print(f"[DEBUG] Aggregated 4H candles: {len(candles_4h)}")
    print(f"[DEBUG] Aggregated 15M candles: {len(candles_15m)}")

    # Ensure that we have enough data for further analysis
    if not candles_4h or not candles_15m:
        print("[ERROR] Insufficient data after aggregation.")
        return []

    # Generate trading signals based on moving averages
    signals = generate_signals(candles_15m, MOVING_AVERAGES)
    
    if not signals:
        print("[ERROR] No valid signals generated.")
        return []

    output_data = []
    
    for signal in signals:
        stop_loss, take_profit = calculate_trade_levels(signal, signal["atr"])
        position_size = calculate_position_size(ACCOUNT_BALANCE, RISK_PERCENTAGE, signal["entry"], stop_loss)
        trailing_stop = apply_trailing_stop(signal["entry"], stop_loss, signal["type"], signal["atr"])

        output_data.append({
            "Signal": signal["type"],
            "Entry": signal["entry"],
            "SL": stop_loss,
            "TP": take_profit,
            "Lot Size": position_size,
            "Trailing SL": trailing_stop,
        })
    
    if output_data:
        print("[DEBUG] Generated output data for signals.")
    else:
        print("[DEBUG] No signals processed.")
    
    return output_data
