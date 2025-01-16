from .constants import PIP_VALUE, RISK_PERCENTAGE
import asyncio
from deriv_api import DerivAPI

async def calculate_risk(entry_price: float, stop_loss: float, token) -> float:
    """
    Calculates position size based on account balance and risk percentage.
    """
    app_id = 65102
    try:
        # Initialize the API
        api = DerivAPI(app_id=app_id)
        authorize = await api.authorize(token)

        # Get account balance
        response = await api.balance()
        balance = response.get('balance', {}).get('balance', 0)

        if balance <= 0:
            print("Balance is zero or negative.")
            return 0.0

        risk_amount = balance * (RISK_PERCENTAGE / 100)
        position_size = risk_amount / abs(entry_price - stop_loss)
        return round(position_size, 2)

    except Exception as e:
        print("Error:", e)
        return -0.0 


def calculate_stop_loss(entry_price: float, signal_type: str, buffer_pips: int) -> float:
    """
    Calculates the stop loss based on entry price and buffer pips.
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
    Calculates the take profit based on the risk distance and reward-to-risk ratio.
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

