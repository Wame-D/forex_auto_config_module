def calculate_position_size(account_balance, risk_percentage, entry_price, stop_loss_price):
    """Calculate the position size based on account balance and risk percentage."""
    risk_amount = (risk_percentage / 100) * account_balance
    pip_risk = abs(entry_price - stop_loss_price)
    position_size = risk_amount / pip_risk
    return round(position_size, 2)


def calculate_trade_levels(signal, atr, risk_to_reward_ratio=3):
    """Calculate the stop loss and take profit levels."""
    entry = signal["entry"]
    atr_multiplier = atr * 1.5
    if signal["type"] == "BUY":
        stop_loss = entry - atr_multiplier
        take_profit = entry + (atr_multiplier * risk_to_reward_ratio)
    else:
        stop_loss = entry + atr_multiplier
        take_profit = entry - (atr_multiplier * risk_to_reward_ratio)
    return stop_loss, take_profit


def apply_trailing_stop(entry, stop_loss, trade_type, atr):
    """Apply a trailing stop loss based on ATR."""
    atr_multiplier = atr * 1.5
    if trade_type == "BUY":
        return max(stop_loss, entry + atr_multiplier)
    elif trade_type == "SELL":
        return min(stop_loss, entry - atr_multiplier)
