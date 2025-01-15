from .constants import PIP_VALUE, RISK_PERCENTAGE, REWARD_TO_RISK_RATIO
def calculate_risk_amount(entry_price: float, stop_loss: float, account_balance: float) -> float:
    """
    Calculates the maximum monetary risk based on account balance and risk percentage.
    """
    if account_balance <= 0 or stop_loss == entry_price:
        raise ValueError("Invalid account balance or stop loss equals entry price.")
    
    return round(account_balance * (RISK_PERCENTAGE / 100), 2)

def calculate_stop_loss(entry_price: float, signal_type: str, buffer_pips: int) -> float:
    """
    Calculates the stop loss based on entry price,signal type and buffer pips.
    """
    buffer = buffer_pips * PIP_VALUE
    if signal_type == "Buy":
        return round(entry_price - buffer, 5)
    elif signal_type == "Sell":
        return round(entry_price + buffer, 5)
    else:
        raise ValueError("Invalid signal type. Must be 'Buy' or 'Sell'.")

def calculate_take_profit(entry_price: float, stop_loss: float, signal_type: str) -> float:
    """
    Calculates the take profit based on the risk distance on entry price, stop loss, and reward-to-risk ratio.
    """
    risk_distance = abs(entry_price - stop_loss)
    if signal_type == "Buy":
        return round(entry_price + (REWARD_TO_RISK_RATIO * risk_distance), 5)
    elif signal_type == "Sell":
        return round(entry_price - (REWARD_TO_RISK_RATIO * risk_distance), 5)
    else:
        raise ValueError("Invalid signal type. Must be 'Buy' or 'Sell'.")

def calculate_position_size(risk_amount: float, entry_price: float, stop_loss: float) -> float:
    """
    Calculates the position size (lot size) based on the risk amount and pip risk.
    """
    pip_risk = abs(entry_price - stop_loss)
    if pip_risk == 0:
        raise ValueError("Stop loss cannot equal entry price.")
    
    return round(risk_amount / (pip_risk / PIP_VALUE), 2)
