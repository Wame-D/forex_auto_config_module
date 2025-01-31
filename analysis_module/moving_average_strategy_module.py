from datetime import datetime
from typing import List, Dict, Any
import logging
from .constants import MOVING_AVERAGE_PERIODS, ATR_PERIOD, REWARD_TO_RISK_RATIO

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def calculate_moving_averages(candles: List[Dict[str, Any]], index: int, periods: Dict[str, int]) -> Dict[str, float]:
    """
    Calculate moving averages for given periods.
    
    Parameters:
        candles (List[Dict[str, Any]]): List of candlestick data containing 'close' prices.
        index (int): Current index in the candlestick list.
        periods (Dict[str, int]): Dictionary mapping period names to their lengths (e.g., "short": 7).
        
    Returns:
        Dict[str, float]: Dictionary of calculated moving averages for each period.
    """
    try:
        # Calculate moving averages only if sufficient data is available
        ma = {
            period: sum(candle["close"] for candle in candles[max(0, index - length):index]) / length
            for period, length in periods.items()
            if index >= length  # Ensure there's enough data for the period
        }
        logger.info(f"Moving averages calculated at index {index}: {ma}")
        return ma
    except Exception as e:
        logger.error(f"Error calculating moving averages: {e}")
        return {}

def check_crossover(prev_ma: Dict[str, float], curr_ma: Dict[str, float]) -> str:
    """
    Check for crossovers between moving averages to generate buy/sell signals.
    
    Buy Signal:
        - 7-period MA crosses above 14-period MA.
        - 89-period MA crosses above 200-period MA.
    
    Sell Signal:
        - 7-period MA crosses below 14-period MA.
        - 89-period MA crosses below 200-period MA.
    
    Parameters:
        prev_ma (Dict[str, float]): Moving averages from the previous candle.
        curr_ma (Dict[str, float]): Moving averages from the current candle.
        
    Returns:
        str: "Buy", "Sell", or an empty string if no crossover is detected.
    """
    try:
        # Check for Buy signal
        if (prev_ma.get("short", 0) < prev_ma.get("mid", 0) and curr_ma.get("short", 0) > curr_ma.get("mid", 0)) and \
           (prev_ma.get("long", 0) < prev_ma.get("very_long", 0) and curr_ma.get("long", 0) > curr_ma.get("very_long", 0)):
            logger.info("Buy signal detected: 7-period MA crossed above 14-period MA, and 89-period MA crossed above 200-period MA.")
            return "Buy"
        
        # Check for Sell signal
        if (prev_ma.get("short", 0) > prev_ma.get("mid", 0) and curr_ma.get("short", 0) < curr_ma.get("mid", 0)) and \
           (prev_ma.get("long", 0) > prev_ma.get("very_long", 0) and curr_ma.get("long", 0) < curr_ma.get("very_long", 0)):
            logger.info("Sell signal detected: 7-period MA crossed below 14-period MA, and 89-period MA crossed below 200-period MA.")
            return "Sell"
        
        logger.debug("No crossover signal detected.")
        return ""
    except Exception as e:
        logger.error(f"Error checking crossovers: {e}")
        return ""

def calculate_atr(candles: List[Dict[str, Any]], index: int, atr_period: int) -> float:
    """
    Calculate the Average True Range (ATR) over the specified period.
    
    Parameters:
        candles (List[Dict[str, Any]]): List of candlestick data containing 'high', 'low', and 'close' prices.
        index (int): Current index in the candlestick list.
        atr_period (int): Number of periods to calculate ATR.
        
    Returns:
        float: Calculated ATR value, or 0 if insufficient data is available.
    """
    try:
        if index < atr_period:
            logger.debug(f"Insufficient data for ATR calculation at index {index}.")
            return 0
        
        # Calculate True Range for each period
        true_ranges = [
            max(
                candles[i]["high"] - candles[i]["low"],  # High - Low
                abs(candles[i]["high"] - candles[i - 1]["close"]),  # High - Previous Close
                abs(candles[i]["low"] - candles[i - 1]["close"])  # Low - Previous Close
            )
            for i in range(index - atr_period, index)
        ]
        
        # Calculate ATR as the average of True Ranges
        atr = sum(true_ranges) / atr_period
        logger.info(f"ATR calculated at index {index}: {atr}")
        return atr
    except Exception as e:
        logger.error(f"Error calculating ATR: {e}")
        return 0

def calculate_sl_tp(entry: float, signal_type: str, atr: float, reward_to_risk_ratio: float) -> Dict[str, float]:
    """
    Calculate Stop Loss (SL) and Take Profit (TP) levels based on ATR.
    
    Parameters:
        entry (float): Entry price for the trade.
        signal_type (str): "Buy" or "Sell" signal type.
        atr (float): Calculated ATR value.
        reward_to_risk_ratio (float): Risk-to-reward ratio for the trade.
        
    Returns:
        Dict[str, float]: Dictionary containing SL and TP values.
    """
    try:
        # Calculate Stop Loss based on signal type
        sl = entry - atr if signal_type == "Buy" else entry + atr
        
        # Calculate Take Profit using the risk-to-reward ratio
        tp = entry + (entry - sl) * reward_to_risk_ratio if signal_type == "Buy" else entry - (sl - entry) * reward_to_risk_ratio
        
        logger.info(f"SL and TP calculated: SL={sl}, TP={tp}")
        return {"SL": round(sl, 5), "TP": round(tp, 5)}
    except Exception as e:
        logger.error(f"Error calculating SL/TP: {e}")
        return {"SL": 0, "TP": 0}

def moving_average_strategy(candles_4h: List[Dict[str, Any]], candles_30m: List[Dict[str, Any]], symbol: str) -> List[Dict[str, Any]]:
    """
    Moving average crossover strategy with multi-timeframe confirmation.
    Generates highly valid signals for backtesting.
    
    Parameters:
        candles_4h (List[Dict[str, Any]]): List of 4-hour candlestick data.
        candles_30m (List[Dict[str, Any]]): List of 30-minute candlestick data.
        symbol (str): Trading pair symbol (e.g., "EURUSD").
        
    Returns:
        List[Dict[str, Any]]: List of generated trading signals.
    """
    logger.info("Starting moving average strategy...")
    
    # Check if there's sufficient data for the 200-period moving average
    if len(candles_4h) < 200:
        print("Insufficient data for 200-period moving average. We need Data For 30 Days Be Patient")  # Single print statement
        return []
    
    signals = []
    try:
        # Iterate through the 4-hour candles starting from index 200 (to ensure sufficient data for 200-period MA)
        for i in range(200, len(candles_4h)):
            # Calculate moving averages for the 4H timeframe
            ma_4h_prev = calculate_moving_averages(candles_4h, i - 1, MOVING_AVERAGE_PERIODS)
            ma_4h_curr = calculate_moving_averages(candles_4h, i, MOVING_AVERAGE_PERIODS)
            
            # Skip if insufficient data for moving averages
            if not ma_4h_prev or not ma_4h_curr:
                logger.debug("Insufficient data to calculate 4H moving averages. Skipping...")
                continue
            
            # Determine trend signal for the 4H timeframe
            signal_type_4h = check_crossover(ma_4h_prev, ma_4h_curr)
            if not signal_type_4h:
                logger.debug(f"No valid 4H trend signal at index {i}. Skipping...")
                continue
            
            # Calculate moving averages for the 30M timeframe
            ma_30m_prev = calculate_moving_averages(candles_30m, len(candles_30m) - 2, MOVING_AVERAGE_PERIODS)
            ma_30m_curr = calculate_moving_averages(candles_30m, len(candles_30m) - 1, MOVING_AVERAGE_PERIODS)
            
            # Skip if insufficient data for moving averages
            if not ma_30m_prev or not ma_30m_curr:
                logger.debug("Insufficient data to calculate 30M moving averages. Skipping...")
                continue
            
            # Determine trend signal for the 30M timeframe
            signal_type_30m = check_crossover(ma_30m_prev, ma_30m_curr)
            if signal_type_4h != signal_type_30m:
                logger.debug(f"4H and 30M signals do not match at index {i}. Skipping...")
                continue
            
            # Calculate entry price and ATR
            entry_price = candles_4h[i]["close"]
            atr = calculate_atr(candles_4h, i, ATR_PERIOD)
            if atr == 0:
                logger.debug(f"Invalid ATR value at index {i}. Skipping...")
                continue
            
            # Calculate Stop Loss and Take Profit levels
            levels = calculate_sl_tp(entry_price, signal_type_4h, atr, REWARD_TO_RISK_RATIO)
            if abs(levels["SL"] - entry_price) < 0.0001 or abs(levels["TP"] - entry_price) < 0.0001:
                logger.debug(f"Invalid SL/TP levels at index {i}. Skipping...")
                continue
            
            # Create and append the signal
            signal = {
                "Pair": symbol,
                "Signal": signal_type_4h,
                "Entry": round(entry_price, 5),
                "SL": levels["SL"],
                "TP": levels["TP"]
            }
            signals.append(signal)
            logger.info(f"Signal generated at index {i}: {signal}")
        
        logger.info(f"Total signals generated: {len(signals)}")
        return signals
    except Exception as e:
        logger.exception(f"Error in moving_average_strategy: {e}")
        return []