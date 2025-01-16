import logging
from typing import List, Dict, Any
from .risk_management import (
    calculate_stop_loss,
    calculate_take_profit,
    calculate_position_size,
)
from .constants import DEFAULT_BUFFER_PIPS, EXOTIC_PAIRS

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def analyze_malaysian_strategy(candles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes market data and generates trade signals based on a strategy.
    """
    logger.info("Starting strategy analysis...")
    signals = []

    try:
        for i in range(1, len(candles)):
            prev_candle = candles[i - 1]
            current_candle = candles[i]

            signal_type = None
            entry_price = current_candle["close"]
            pair = current_candle.get("pair", "Unknown")

            # Skip exotic pairs
            if pair in EXOTIC_PAIRS:
                logger.warning(f"Skipping exotic pair: {pair}")
                continue

            # Determine signal type
            if current_candle["close"] > prev_candle["high"]:  # Bullish breakout
                signal_type = "Buy"
            elif current_candle["close"] < prev_candle["low"]:  # Bearish breakdown
                signal_type = "Sell"

            if signal_type:
                stop_loss = calculate_stop_loss(entry_price, signal_type, DEFAULT_BUFFER_PIPS)
                take_profit = calculate_take_profit(entry_price, stop_loss, signal_type)

                # Append signal details
                signals.append({
                    "Pair": pair,
                    "Signal": signal_type,
                    "Entry": round(entry_price, 5),
                    "SL": round(stop_loss, 5),
                    "TP": round(take_profit, 5),
                    "Risk Amount": 1,
                    "Position Size": 1,
                })

        logger.info(f"Generated {len(signals)} signals.")
        return {
            "status": "success",
            "message": "Strategy analysis completed.",
            "data": signals,
        }

    except Exception as e:
        logger.exception("Error during strategy analysis.")
        return {
            "status": "error",
            "message": str(e),
            "data": [],
        }
