from datetime import timedelta
from typing import List, Dict, Any
from .risk_management import calculate_stop_loss, calculate_take_profit
from .constants import ATR_PERIOD, ADX_THRESHOLD, HIGH_RISK_RATIO


def moving_average_strategy(candles_4h: List[Dict[str, Any]], candles_30m: List[Dict[str, Any]],symbol: str) -> List[Dict[str, Any]]:
    """Simplified moving average strategy with trend and volatility confirmation."""
    signals = []

    try:
        for i in range(1, len(candles_4h)):
            current_candle = candles_4h[i]
            prev_candle = candles_4h[i - 1]
            entry_price = current_candle["close"]
            pair = symbol

            # Calculate Moving Averages (7, 14, 89, 200 periods)
            short_ma, mid_ma, long_ma, long_term_ma = calculate_moving_averages(candles_4h, i)

            # Check for trend alignment (Moving Averages)
            signal_type = get_trend_signal(short_ma, mid_ma, long_ma, long_term_ma)
            if not signal_type:
                continue

            # Calculate ATR for volatility
            atr = calculate_atr(candles_4h, ATR_PERIOD)

            # Skip trades in choppy markets (ADX < 20)
            if calculate_adx(candles_4h, ATR_PERIOD) < ADX_THRESHOLD:
                continue

            # Validate Safe Zone based on ATR
            safe_zone_data = calculate_safe_zone(current_candle, signal_type, atr)

            # Validate price action on 30-minute chart
            if not is_valid_price_action(candles_30m, current_candle, signal_type, safe_zone_data, atr):
                continue

            # Calculate Stop Loss and Take Profit based on ATR
            stop_loss, take_profit = calculate_sl_tp(entry_price, signal_type, atr)

            if stop_loss == entry_price or take_profit == entry_price:
                continue

            # Create and append the trading signal
            signals.append(create_signal(pair, signal_type, entry_price, stop_loss, take_profit))

        return signals

    except Exception:
        return []


def calculate_moving_averages(candles: List[Dict[str, Any]], index: int) -> tuple:
    """Calculate short, mid, long, and long-term moving averages."""
    short_ma = sum(candle["close"] for candle in candles[max(0, index - 7):index]) / 7
    mid_ma = sum(candle["close"] for candle in candles[max(0, index - 14):index]) / 14
    long_ma = sum(candle["close"] for candle in candles[max(0, index - 89):index]) / 89
    long_term_ma = sum(candle["close"] for candle in candles[max(0, index - 200):index]) / 200
    return short_ma, mid_ma, long_ma, long_term_ma


def get_trend_signal(short_ma: float, mid_ma: float, long_ma: float, long_term_ma: float) -> str:
    """Return 'Buy' or 'Sell' signal based on trend alignment."""
    if short_ma > mid_ma > long_ma > long_term_ma:
        return "Buy"
    elif short_ma < mid_ma < long_ma < long_term_ma:
        return "Sell"
    return ""


def calculate_atr(candles: List[Dict[str, Any]], period: int) -> float:
    """Calculate Average True Range (ATR) for volatility-based risk management."""
    tr_values = [
        max(candle["high"] - candle["low"], abs(candle["high"] - candles[i - 1]["close"]),
            abs(candle["low"] - candles[i - 1]["close"]))
        for i, candle in enumerate(candles[1:], 1)
    ]
    return sum(tr_values[-period:]) / period


def calculate_adx(candles: List[Dict[str, Any]], period: int) -> float:
    """Calculate Average Directional Index (ADX) to measure trend strength."""
    try:
        dm_plus, dm_minus, tr = get_directional_movement(candles)
        smoothed_dm_plus = sum(dm_plus[-period:]) / period
        smoothed_dm_minus = sum(dm_minus[-period:]) / period
        smoothed_tr = sum(tr[-period:]) / period
        return 100 * abs(smoothed_dm_plus - smoothed_dm_minus) / smoothed_tr if smoothed_tr else 0
    except Exception:
        return 0


def get_directional_movement(candles: List[Dict[str, Any]]) -> tuple:
    """Calculate directional movements (DM+ and DM-) and True Range (TR)."""
    dm_plus = [candles[i]["high"] - candles[i - 1]["high"] for i in range(1, len(candles))]
    dm_minus = [candles[i - 1]["low"] - candles[i]["low"] for i in range(1, len(candles))]
    tr = [max(candles[i]["high"] - candles[i]["low"], abs(candles[i]["high"] - candles[i - 1]["close"]),
              abs(candles[i]["low"] - candles[i - 1]["close"])) for i in range(1, len(candles))]
    return dm_plus, dm_minus, tr


def calculate_safe_zone(candle: Dict[str, Any], signal_type: str, atr: float) -> Dict[str, Any]:
    """Calculate the safe zone for entry based on ATR."""
    if signal_type == "Buy":
        support_level = candle["low"]
        safe_zone_top = support_level + (atr * 0.75)
        safe_zone_bottom = support_level - (atr * 0.75)
    elif signal_type == "Sell":
        resistance_level = candle["high"]
        safe_zone_top = resistance_level + (atr * 0.75)
        safe_zone_bottom = resistance_level - (atr * 0.75)
    return {"safe_zone_top": safe_zone_top, "safe_zone_bottom": safe_zone_bottom}


def is_valid_price_action(candles: List[Dict[str, Any]], current_candle: Dict[str, Any], signal_type: str,
                           safe_zone_data: Dict[str, Any], atr: float) -> bool:
    """Check if price action on 30-minute chart is valid."""
    return any(
        is_valid_signal(candle, signal_type, safe_zone_data["safe_zone_top"], safe_zone_data["safe_zone_bottom"], atr)
        for candle in candles if candle["timestamp"] >= current_candle["timestamp"] - timedelta(hours=2)
    )


def is_valid_signal(candle: Dict[str, Any], signal_type: str, safe_zone_top: float, safe_zone_bottom: float, atr: float) -> bool:
    """Check if the signal respects the safe zone and volatility."""
    if signal_type == "Buy":
        return candle["low"] >= safe_zone_bottom and candle["high"] <= safe_zone_top
    elif signal_type == "Sell":
        return candle["high"] <= safe_zone_top and candle["low"] >= safe_zone_bottom
    return False


def calculate_sl_tp(entry_price: float, signal_type: str, atr: float) -> tuple:
    """Calculate Stop Loss and Take Profit based on ATR."""
    stop_loss = calculate_stop_loss(entry_price, signal_type, atr * 1.5)
    take_profit = calculate_take_profit(entry_price, stop_loss, signal_type, HIGH_RISK_RATIO)
    return stop_loss, take_profit


def create_signal(pair: str, signal_type: str, entry_price: float, stop_loss: float, take_profit: float) -> Dict[str, Any]:
    """Create the trading signal."""
    return {
        "Pair": pair,
        "Signal": signal_type,
        "Entry": round(entry_price, 5),
        "SL": round(stop_loss, 5),
        "TP": round(take_profit, 5),
    }
