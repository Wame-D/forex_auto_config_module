from django.apps import AppConfig
import asyncio
import threading

from trade.continuousTradeMonitor import monitor_trades

class TradeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trade"

    def ready(self):
        """
        This method runs when the Django app is ready.
        It starts the monitor_trades function in a separate thread.
        """
        print("[Django Startup] Starting trade monitoring service...")
        thread = threading.Thread(target=asyncio.run, args=(monitor_trades(),))
        thread.daemon = True  # Ensures the thread stops when Django stops
        thread.start()



