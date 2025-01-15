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
