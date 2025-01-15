import logging
from datetime import timedelta
from typing import List, Dict, Any
from .risk_management import calculate_risk_amount, calculate_stop_loss, calculate_take_profit
from .constants import ACCOUNT_BALANCE

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def analyze_malaysian_strategy(candles_4h: List[Dict[str, Any]], candles_15m: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes forex data using the Malaysian Forex Strategy.
    Identifies buy and sell signals, calculates stop loss, take profit, and trade amount.
    Returns a JSON object containing the signals and their details.
    """
    logger.info("Starting analysis for Malaysian Forex Strategy...")
    signals = []

    try:
        for i in range(1, len(candles_4h)):
            prev_candle = candles_4h[i - 1]
            current_candle = candles_4h[i]

            signal_type = None
            entry_price = current_candle["close"]

            # Determine signal type
            if current_candle["close"] > prev_candle["high"]:  # Bullish breakout
                signal_type = "Buy"
            elif current_candle["close"] < prev_candle["low"]:  # Bearish breakdown
                signal_type = "Sell"

            if signal_type:
                # Calculate stop loss and take profit
                stop_loss = calculate_stop_loss(entry_price, signal_type, buffer_pips=10)
                take_profit = calculate_take_profit(entry_price, stop_loss, signal_type)

                # Ensure SL and TP are not equal to Entry
                if stop_loss == entry_price or take_profit == entry_price:
                    logger.warning(f"Invalid SL/TP values for signal at index {i}. Skipping...")
                    continue

                # Calculate trade amount
                trade_amount = calculate_risk_amount(entry_price, stop_loss, ACCOUNT_BALANCE)

                # Append the signal
                signals.append({
                    "Signal": signal_type,
                    "Entry": round(entry_price, 5),
                    "SL": round(stop_loss, 5),
                    "TP": round(take_profit, 5),
                    "Amount": trade_amount,
                })

        logger.info(f"Generated {len(signals)} signals.")
        return {
            "status": "success",
            "message": "Trading signals generated successfully.",
            "data": signals
        }

    except Exception as e:
        logger.exception(f"Error analyzing strategy: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }
