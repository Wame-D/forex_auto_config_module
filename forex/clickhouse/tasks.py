
import pytz  # Import pytz for timezone handling
import asyncio
import threading

from authorise_deriv.views import balance
from .user_eligibility_checker import  auto_trading_monitor
from .balance_tracker import balance__tracker
from .account_enabler import enable_disable_accounts

# startimg candle fetching automatically
def start_candle_fetcher():
    """
    Start the candle fetching process concurrently in a background thread.
    """
    def thread_function():
        # Create a new event loop for the thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async tasks
        loop.run_until_complete(
            asyncio.gather(
                enable_disable_accounts(),
                auto_trading_monitor(),
                balance__tracker(),
            )
        )
        
    # Start the thread to run the async tasks
    thread = threading.Thread(target=thread_function)
    thread.start()
