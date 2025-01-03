from datetime import datetime, timedelta
from typing import List, Dict
import asyncio
import pytz
from forex.clickhouse.connection import get_clickhouse_client
# Constants
PIP_VALUE = 0.0002  # For calculating safe zone adjustments
ACCOUNT_BALANCE = 10000  # Account balance for position sizing
RISK_PERCENTAGE = 2  # Risk percentage per trade

# Helper Functions for Aggregation
def aggregate_candles(candles: List[dict], interval_minutes: int) -> List[dict]:
    """
    Aggregate 1-minute candles into larger timeframe candles (e.g., 4-hour or 15-minute).
    """
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

            # Initialize new interval
            start_time = current_time.replace(minute=(current_time.minute // interval_minutes) * interval_minutes, second=0, microsecond=0)
            open_price = candle["open"]
            high_price = candle["high"]
            low_price = candle["low"]
            close_price = candle["close"]
        else:
            # Update high, low, and close for the current interval
            high_price = max(high_price, candle["high"])
            low_price = min(low_price, candle["low"])
            close_price = candle["close"]

    # Append the final interval
    if start_time is not None:
        aggregated.append({
            "timestamp": start_time.isoformat(),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
        })

    return aggregated

# Analysis Functions
def find_key_patterns(data: List[dict]):
    """
    Find key patterns (support or resistance) based on 4-hour candles.
    """
    key_patterns = []
    for i in range(1, len(data)):
        current = data[i]
        previous = data[i - 1]

        if previous['close'] > previous['open'] and current['close'] < current['open']:  # Bearish to Bullish
            key_patterns.append({"pattern": "support", "timestamp": current["timestamp"], "candle": current})
        elif previous['close'] < previous['open'] and current['close'] > current['open']:  # Bullish to Bearish
            key_patterns.append({"pattern": "resistance", "timestamp": current["timestamp"], "candle": current})

    return key_patterns

def confirm_pattern(data: List[dict], pattern: dict) -> bool:
    """
    Confirm the identified pattern using 15-minute candles.
    """
    pattern_time = datetime.fromisoformat(pattern["timestamp"])
    confirmation_candles = [
        candle for candle in data
        if datetime.fromisoformat(candle["timestamp"]) >= pattern_time
    ]

    # Look for small bullish/bearish patterns in 15-minute candles
    for candle in confirmation_candles:
        if pattern["pattern"] == "support" and candle["close"] > candle["open"]:  # Bullish confirmation
            return True
        elif pattern["pattern"] == "resistance" and candle["close"] < candle["open"]:  # Bearish confirmation
            return True

    return False

def calculate_safe_zone(candle: dict, pattern_type: str):
    """
    Calculate the safe zone for the identified pattern.
    """
    if pattern_type == "support":
        entry_price = candle['close'] + PIP_VALUE
        stop_loss = entry_price - (PIP_VALUE * 2)
        take_profit = entry_price + (PIP_VALUE * 4)
    elif pattern_type == "resistance":
        entry_price = candle['close'] - PIP_VALUE
        stop_loss = entry_price + (PIP_VALUE * 2)
        take_profit = entry_price - (PIP_VALUE * 4)
    else:
        raise ValueError("Invalid pattern type")
    
    return {"entry": entry_price, "stop_loss": stop_loss, "take_profit": take_profit}

def calculate_position_size(account_balance: float, risk_percentage: float, entry: float, stop_loss: float):
    """
    Calculate the position size based on account balance, risk percentage, and safe zone.
    """
    risk_amount = account_balance * (risk_percentage / 100)
    pip_risk = abs(entry - stop_loss)
    position_size = risk_amount / pip_risk
    return round(position_size, 2)

def analyze_and_generate_signals(forex_data: List[dict]):
    """
    Perform analysis and generate trading signals based on the Malaysian Forex Strategy.
    """
    # Aggregate candles into 4-hour and 15-minute timeframes
    candles_4h = aggregate_candles(forex_data, interval_minutes=240)
    candles_15m = aggregate_candles(forex_data, interval_minutes=15)

    # Identify patterns on the 4-hour chart
    patterns = find_key_patterns(candles_4h)
    signals = []

    for pattern in patterns:
        if confirm_pattern(candles_15m, pattern):  # Confirm with 15-minute candles
            safe_zone = calculate_safe_zone(pattern['candle'], pattern['pattern'])
            entry_amount = calculate_position_size(
                account_balance=ACCOUNT_BALANCE,
                risk_percentage=RISK_PERCENTAGE,
                entry=safe_zone['entry'],
                stop_loss=safe_zone['stop_loss']
            )
            signals.append({
                "pattern": pattern['pattern'],
                "timestamp": pattern['timestamp'],
                "safe_zone": safe_zone,
                "entry_amount": entry_amount
            })

    return signals

def fetch_data_from_clickhouse(table_name: str, start_time: str, end_time: str):
    """
    Fetch forex data from the ClickHouse database.
    """
    client = get_clickhouse_client()
    query = f"""
        SELECT timestamp, open, high, low, close
        FROM {table_name}
        WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'
        ORDER BY timestamp ASC
    """
    result = client.query(query)

    # Ensure result is iterable
    if hasattr(result, "result_rows"):
        return result.result_rows  # Replace with the correct attribute/method for rows
    elif isinstance(result, list):
        return result
    else:
        raise ValueError("Unexpected query result format.")

# Fetch Data and Analyze
async def fetch_and_analyze_forex_data(start_time: str):
    """
    Fetch forex data and analyze based on the Malaysian Forex Strategy.
    """
    table_name = "candles"
    raw_data = fetch_data_from_clickhouse(
        table_name=table_name, 
        start_time=start_time, 
        end_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )

    # Format data for analysis
    forex_data = [
        {
            "timestamp": row[0].strftime("%Y-%m-%dT%H:%M:%SZ"),  # ISO 8601 timestamp
            "open": row[1],
            "high": row[2],
            "low": row[3],
            "close": row[4],
        }
        for row in raw_data
    ]

    # Perform analysis
    signals = analyze_and_generate_signals(forex_data)

    # Display results
    for signal in signals:
        print(f"Pattern: {signal['pattern']} at {signal['timestamp']}")
        print(f"Safe Zone: Entry at {signal['safe_zone']['entry']}, Stop Loss at {signal['safe_zone']['stop_loss']}, Take Profit at {signal['safe_zone']['take_profit']}")
        print(f"Position Size: {signal['entry_amount']} units")
        print()

# Main Execution
if __name__ == "__main__":
    async def main():
        # Specify the desired start time for fetching data
        start_time = "2025-01-01 00:00:00"  # Example start time
        await fetch_and_analyze_forex_data(start_time)

    asyncio.run(main())
