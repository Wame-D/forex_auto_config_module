from .constants import PIP_VALUE, ACCOUNT_BALANCE, RISK_PERCENTAGE

def calculate_risk(entry_price: float, stop_loss: float) -> float:
    """
    Calculates position size based on account balance and risk percentage.
    """
    risk_amount = ACCOUNT_BALANCE * (RISK_PERCENTAGE / 100)
    position_size = risk_amount / abs(entry_price - stop_loss)
    return round(position_size, 2)
