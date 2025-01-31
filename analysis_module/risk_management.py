import asyncio
import logging
from deriv_api import DerivAPI
from .constants import PIP_VALUE, RISK_PERCENTAGE, REWARD_TO_RISK_RATIO
from authorise_deriv.views import balance

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def calculate_risk(token: float, entry_price: float, stop_loss: float) -> float:
    """
    Calculates the maximum monetary risk based on account balance and risk percentage.
    """
    try:

        account_balance = balance(token)
        if account_balance <= 0 or stop_loss == entry_price:
            logger.warning("Invalid account balance or stop loss equals entry price.")
            return 0.0

        # Calculate the risk amount based on account balance and risk percentage
        risk_amount = account_balance * (RISK_PERCENTAGE / 100)
        return round(risk_amount, 2)

    except Exception as e:
        logger.error(f"Error in calculate_risk_amount: {e}")
        return 0.0  # Return 0 if error occurs

def calculate_stop_loss(entry_price: float, signal_type: str, buffer_pips: int) -> float:
    """
    Calculates the stop loss based on entry price, signal type, and buffer pips.
    """
    if buffer_pips <= 0:
        logger.error("Buffer pips must be greater than zero.")
        raise ValueError("Buffer pips must be greater than zero.")
        
    buffer = buffer_pips * PIP_VALUE
    
    if signal_type == "Buy":
        stop_loss = round(entry_price - buffer, 5)
    elif signal_type == "Sell":
        stop_loss = round(entry_price + buffer, 5)
    else:
        # logger.error("Invalid signal type. Must be 'Buy' or 'Sell'.")
        raise ValueError("Invalid signal type. Must be 'Buy' or 'Sell'.")
    
    logger.info(f"Calculated stop loss: {stop_loss}")
    return stop_loss

def calculate_take_profit(entry_price: float, stop_loss: float, signal_type: str, reward_to_risk: float) -> float:
    """
    Calculates the take profit based on the risk distance, entry price, stop loss, and reward-to-risk ratio.
    """
    if entry_price == stop_loss:
        logger.error("Stop loss cannot equal entry price.")
        raise ValueError("Stop loss cannot equal entry price.")

    risk_distance = abs(entry_price - stop_loss)
    if risk_distance == 0:
        logger.error("Risk distance cannot be zero.")
        raise ValueError("Risk distance cannot be zero.")
    
    if signal_type == "Buy":
        take_profit = round(entry_price + (reward_to_risk * risk_distance), 5)
    elif signal_type == "Sell":
        take_profit = round(entry_price - (reward_to_risk * risk_distance), 5)
    else:
        logger.error("Invalid signal type. Must be 'Buy' or 'Sell'.")
        raise ValueError("Invalid signal type. Must be 'Buy' or 'Sell'.")
    
    logger.info(f"Calculated take profit: {take_profit}")
    return take_profit

def calculate_position_size(risk_amount: float, entry_price: float, stop_loss: float) -> float:
    """
    Calculates the position size (lot size) based on the risk amount and pip risk.
    """
    if stop_loss == entry_price:
        logger.error("Stop loss cannot equal entry price.")
        raise ValueError("Stop loss cannot equal entry price.")
    
    pip_risk = abs(entry_price - stop_loss)
    if pip_risk == 0:
        logger.error("Pip risk cannot be zero.")
        raise ValueError("Pip risk cannot be zero.")
    
    position_size = risk_amount / (pip_risk / PIP_VALUE)
    position_size = round(position_size, 2)

    logger.info(f"Calculated position size: {position_size}")
    return position_size
