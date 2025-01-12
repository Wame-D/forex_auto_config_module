from datetime import datetime, timedelta
from forex.clickhouse.connection import get_clickhouse_client
from .strategy import aggregate_candles, generate_signals
from .risk_management import calculate_position_size, calculate_trade_levels, apply_trailing_stop

PIP_VALUE = 0.0001
ACCOUNT_BALANCE = 10000
RISK_PERCENTAGE = 2
MOVING_AVERAGES = [7, 14, 89, 200]
ATR_PERIOD = 14
TIMEFRAMES = {"4H": 240, "15M": 15}

async def fetch_data_from_clickhouse(table_name: str, start_time: str, end_time: str):
    """Fetch data from ClickHouse database."""
    client = get_clickhouse_client()
    query = f"""
        SELECT timestamp, open, high, low, close
        FROM {table_name}
        WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'
        ORDER BY timestamp ASC
    """
    try:
        result = client.query(query)
        rows = result.result_rows
        if not rows:
            print(f"[DEBUG] No data found between {start_time} and {end_time}.")
            return []  # Return empty if no data found

        return [
            {
                "timestamp": row[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": row[1],
                "high": row[2],
                "low": row[3],
                "close": row[4],
            }
            for row in rows
        ]
    except Exception as e:
        print(f"[ERROR] Error fetching data: {e}")
        return []  # Return an empty list if any error occurs

def aggregate_candles(candles, interval_minutes):
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
        print("[DEBUG] No candles aggregated.")
    else:
        print(f"[DEBUG] Aggregated candles into {len(aggregated)} intervals.")
        
    return aggregated

def find_key_patterns(data):
    """Find candlestick patterns such as support and resistance."""
    key_patterns = []
    for i in range(1, len(data)):
        current = data[i]
        previous = data[i - 1]
        if previous['close'] > previous['open'] and current['close'] < current['open']:
            print(f"[DEBUG] Found support pattern at {current['timestamp']}")
            key_patterns.append({"pattern": "support", "timestamp": current["timestamp"], "candle": current})
        elif previous['close'] < previous['open'] and current['close'] > current['open']:
            print(f"[DEBUG] Found resistance pattern at {current['timestamp']}")
            key_patterns.append({"pattern": "resistance", "timestamp": current["timestamp"], "candle": current})
    
    if not key_patterns:
        print("[DEBUG] No key patterns found.")
    
    return key_patterns

async def fetch_and_analyze_forex_data(start_time="2025-01-01 00:00:00"):
    """Fetch forex data and analyze it based on the Malaysian Forex Strategy."""
    table_name = "candles"
    end_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    # Fetch data from the ClickHouse database
    raw_data = await fetch_data_from_clickhouse(table_name, start_time, end_time)
    
    if not raw_data:
        print("[ERROR] No data available for the given time range.")
        return []

    # Aggregate candles into different timeframes
    candles_4h = aggregate_candles(raw_data, TIMEFRAMES["4H"])
    candles_15m = aggregate_candles(raw_data, TIMEFRAMES["15M"])

    if not candles_4h or not candles_15m:
        print("[ERROR] Insufficient data after aggregation.")
        return []

    # Generate trading signals based on selected strategy
    signals = generate_signals(candles_4h, candles_15m, MOVING_AVERAGES, ATR_PERIOD, strategy_choice="malaysian")
    
    if not signals:
        print("[ERROR] No valid signals generated.")
        return []

    output_data = []
    
    for signal in signals:
        stop_loss, take_profit = calculate_trade_levels(signal, signal["atr"])
        position_size = calculate_position_size(ACCOUNT_BALANCE, RISK_PERCENTAGE, signal["entry"], stop_loss)
        trailing_stop = apply_trailing_stop(signal["entry"], stop_loss, signal["type"], signal["atr"])

        # Add the processed signal to the output_data list
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
