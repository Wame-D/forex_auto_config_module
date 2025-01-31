import logging
from .constants import PIP_VALUE, RISK_PERCENTAGE, REWARD_TO_RISK_RATIO
from authorise_deriv.views import balance

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def calculate_risk(token: float, entry_price: float, stop_loss: float) -> float:
    """
    Calculates the maximum monetary risk based on the account balance and risk percentage.
    
    Args:
        token (float): The authentication token for accessing the account balance.
        entry_price (float): The entry price of the trade.
        stop_loss (float): The stop loss price of the trade.
    
    Returns:
        float: The risk amount rounded to 2 decimal places.
    
    Raises:
        ValueError: If the account balance is invalid or stop loss equals entry price.
    """
    try:
        # Fetch the account balance using the provided token
        account_balance = balance(token)
        
        # Validate account balance
        if account_balance <= 0:
            logger.warning("Invalid account balance. Balance must be greater than zero.")
            return 0.0
        
        # Ensure stop loss is not equal to entry price
        if stop_loss == entry_price:
            logger.warning("Stop loss cannot equal entry price.")
            return 0.0

        # Calculate the risk amount based on the account balance and risk percentage
        risk_amount = account_balance * (RISK_PERCENTAGE / 100)
        return round(risk_amount, 2)  # Round to 2 decimal places for monetary value

    except Exception as e:
        logger.error(f"Error in calculate_risk: {e}")
        return 0.0  # Return 0 if an error occurs

def calculate_stop_loss(entry_price: float, signal_type: str, buffer_pips: int) -> float:
    """
    Calculates the stop loss based on the entry price, signal type, and buffer pips.
    
    Args:
        entry_price (float): The entry price of the trade.
        signal_type (str): The type of signal, either "Buy" or "Sell".
        buffer_pips (int): The number of pips to use as a buffer for the stop loss.
    
    Returns:
        float: The stop loss price rounded to 4 decimal places.
    
    Raises:
        ValueError: If buffer pips are invalid or signal type is incorrect.
    """
    # Validate buffer pips
    if buffer_pips <= 0:
        logger.error("Buffer pips must be greater than zero.")
        raise ValueError("Buffer pips must be greater than zero.")
    
    # Calculate the buffer in price terms
    buffer = buffer_pips * PIP_VALUE
    
    # Calculate stop loss based on signal type
    if signal_type == "Buy":
        stop_loss = entry_price - buffer  # Stop loss below entry for Buy
    elif signal_type == "Sell":
        stop_loss = entry_price + buffer  # Stop loss above entry for Sell
    else:
        logger.error("Invalid signal type. Must be 'Buy' or 'Sell'.")
        raise ValueError("Invalid signal type. Must be 'Buy' or 'Sell'.")
    
    # Ensure stop loss is not equal to entry price
    if stop_loss == entry_price:
        logger.error("Stop loss cannot equal entry price.")
        raise ValueError("Stop loss cannot equal entry price.")
    
    # Round stop loss to 4 decimal places to match candle prices
    stop_loss = round(stop_loss, 4)
    logger.info(f"Calculated stop loss: {stop_loss}")
    return stop_loss

def calculate_take_profit(entry_price: float, stop_loss: float, signal_type: str, reward_to_risk: float) -> float:
    """
    Calculates the take profit based on the entry price, stop loss, signal type, and reward-to-risk ratio.
    
    Args:
        entry_price (float): The entry price of the trade.
        stop_loss (float): The stop loss price of the trade.
        signal_type (str): The type of signal, either "Buy" or "Sell".
        reward_to_risk (float): The desired reward-to-risk ratio.
    
    Returns:
        float: The take profit price rounded to 4 decimal places.
    
    Raises:
        ValueError: If stop loss equals entry price or risk distance is zero.
    """
    # Ensure stop loss is not equal to entry price
    if entry_price == stop_loss:
        logger.error("Stop loss cannot equal entry price.")
        raise ValueError("Stop loss cannot equal entry price.")

    # Calculate the risk distance (absolute difference between entry and stop loss)
    risk_distance = abs(entry_price - stop_loss)
    if risk_distance == 0:
        logger.error("Risk distance cannot be zero.")
        raise ValueError("Risk distance cannot be zero.")
    
    # Calculate take profit based on signal type and reward-to-risk ratio
    if signal_type == "Buy":
        take_profit = entry_price + (reward_to_risk * risk_distance)  # TP above entry for Buy
    elif signal_type == "Sell":
        take_profit = entry_price - (reward_to_risk * risk_distance)  # TP below entry for Sell
    else:
        logger.error("Invalid signal type. Must be 'Buy' or 'Sell'.")
        raise ValueError("Invalid signal type. Must be 'Buy' or 'Sell'.")
    
    # Ensure take profit is not equal to entry price
    if take_profit == entry_price:
        logger.error("Take profit cannot equal entry price.")
        raise ValueError("Take profit cannot equal entry price.")
    
    # Round take profit to 4 decimal places to match candle prices
    take_profit = round(take_profit, 4)
    logger.info(f"Calculated take profit: {take_profit}")
    return take_profit

def calculate_position_size(risk_amount: float, entry_price: float, stop_loss: float) -> float:
    """
    Calculates the position size (lot size) based on the risk amount, entry price, and stop loss.
    
    Args:
        risk_amount (float): The monetary risk amount.
        entry_price (float): The entry price of the trade.
        stop_loss (float): The stop loss price of the trade.
    
    Returns:
        float: The position size rounded to 2 decimal places.
    
    Raises:
        ValueError: If stop loss equals entry price or pip risk is zero.
    """
    # Ensure stop loss is not equal to entry price
    if stop_loss == entry_price:
        logger.error("Stop loss cannot equal entry price.")
        raise ValueError("Stop loss cannot equal entry price.")
    
    # Calculate the pip risk (absolute difference between entry and stop loss)
    pip_risk = abs(entry_price - stop_loss)
    if pip_risk == 0:
        logger.error("Pip risk cannot be zero.")
        raise ValueError("Pip risk cannot be zero.")
    
    # Calculate position size using the formula: risk_amount / (pip_risk / PIP_VALUE)
    position_size = risk_amount / (pip_risk / PIP_VALUE)
    position_size = round(position_size, 2)  # Round to 2 decimal places for lot size

    logger.info(f"Calculated position size: {position_size}")
    return position_size