import logging
from datetime import timedelta
from typing import List, Dict, Any
from .constants import REWARD_TO_RISK_RATIO, PIP_VALUE

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def analyze_malaysian_strategy(candles_4h: List[Dict[str, Any]], candles_15m: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyzes forex data using the Malaysian Forex Strategy.
    Identifies buy and sell signals and calculates stop loss, take profit, and lot size.
    Returns a list of trading signals.
    """
    logger.info("Analyzing Malaysian Forex Strategy...")
    signals = []
    try:
        for i in range(1, len(candles_4h)):
            prev_candle = candles_4h[i - 1]
            current_candle = candles_4h[i]

            signal_type = None
            entry_price = None

            if current_candle["close"] > prev_candle["high"]:  # Breakout condition
                signal_type = "Buy"
                entry_price = current_candle["close"]
            elif current_candle["close"] < prev_candle["low"]:  # Breakdown condition
                signal_type = "Sell"
                entry_price = current_candle["close"]

            if signal_type:
                start_time = current_candle["timestamp"]
                end_time = start_time + timedelta(hours=4)
                segment = [c for c in candles_15m if start_time <= c["timestamp"] < end_time]

                confirmation = any(
                    (signal_type == "Buy" and c["close"] > c["open"]) or
                    (signal_type == "Sell" and c["close"] < c["open"]) for c in segment
                )

                if confirmation:
                    stop_loss = (
                        entry_price - (prev_candle["high"] - prev_candle["low"]) * PIP_VALUE
                        if signal_type == "Buy"
                        else entry_price + (prev_candle["high"] - prev_candle["low"]) * PIP_VALUE
                    )
                    take_profit = (
                        entry_price + REWARD_TO_RISK_RATIO * (entry_price - stop_loss)
                        if signal_type == "Buy"
                        else entry_price - REWARD_TO_RISK_RATIO * (stop_loss - entry_price)
                    )

                    signals.append({
                        "Signal": signal_type,
                        "Entry": round(entry_price, 2),
                        "SL": round(stop_loss, 2),
                        "TP": round(take_profit, 2),
                        "Lot Size": 0,
                    })

        logger.info(f"Generated {len(signals)} signals.")
        return signals
    except Exception as e:
        logger.exception(f"Error analyzing strategy: {e}")
        return []
