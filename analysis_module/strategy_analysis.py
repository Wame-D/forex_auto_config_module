import logging
from typing import List, Dict, Any
from .risk_management import (
    calculate_risk_amount,
    calculate_stop_loss,
    calculate_take_profit,
    calculate_position_size,
)
from .constants import ACCOUNT_BALANCE, DEFAULT_BUFFER_PIPS, EXOTIC_PAIRS

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def analyze_strategy(candles: List[Dict[str, Any]]) -> Dict[str, Any]:
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
                # Calculate risk, SL, TP, and position size
                risk_amount = calculate_risk_amount(ACCOUNT_BALANCE)
                stop_loss = calculate_stop_loss(entry_price, signal_type, DEFAULT_BUFFER_PIPS)
                take_profit = calculate_take_profit(entry_price, stop_loss, signal_type)
                position_size = calculate_position_size(risk_amount, entry_price, stop_loss)

                # Append signal details
                signals.append({
                    "Pair": pair,
                    "Signal": signal_type,
                    "Entry": round(entry_price, 5),
                    "SL": round(stop_loss, 5),
                    "TP": round(take_profit, 5),
                    "Risk Amount": risk_amount,
                    "Position Size": position_size,
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
