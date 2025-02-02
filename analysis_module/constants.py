# -*- coding: utf-8 -*-
"""
This module defines all constants used across the trading system.
Constants are grouped by functionality for better readability and maintainability.
"""

import pytz

# ===============================
# Timeframe Settings
# ===============================
TIMEFRAMES = {
    "4H": 240,   # 4-hour chart timeframe (240 minutes)
    "15M": 15,   # 15-minute chart timeframe
    "30M": 30    # 30-minute chart timeframe
}
"""
TIMEFRAMES:
    Defines the timeframes used for chart analysis. Each key represents a human-readable 
    timeframe (e.g., "4H" for 4 hours), and the value is the equivalent duration in minutes.

    Purpose:
        Specifies the time intervals for analyzing price movements on charts.

    Effect:
        Determines the granularity of data used for technical analysis and trade decisions.

    Example:
        - "4H": Used for long-term trend analysis.
        - "15M": Used for short-term intraday trading.
"""

# ===============================
# Risk Management Constants
# ===============================
PIP_VALUE = 0.0001
"""
PIP_VALUE:
    Represents the value of a single pip in decimal format. Used to calculate price movements 
    and position sizing.

    Purpose:
        Standardizes the smallest unit of price movement for consistent calculations.

    Effect:
        Affects the precision of stop loss, take profit, and risk management calculations.

    Example:
        For EUR/USD, a pip value of 0.0001 means each pip corresponds to $0.0001 per unit traded.
"""

RISK_PERCENTAGE = 0.02  # Set to 2%
"""
RISK_PERCENTAGE:
    The percentage of the account balance to risk per trade. For example, 0.02 means 2% of 
    the account balance is allocated for each trade.

    Purpose:
        Limits the maximum risk exposure per trade to protect the trading account.

    Effect:
        Controls the size of positions based on the trader's risk tolerance.

    How to Test:
        - Increase to 0.03 (3%) for higher risk tolerance.
        - Decrease to 0.01 (1%) for more conservative trading.
"""

REWARD_TO_RISK_RATIO = 1
"""
REWARD_TO_RISK_RATIO:
    The reward-to-risk ratio determines the profit target relative to the risk. A value of 2 
    means for every 1 unit risked, the trader aims for 2 units of profit.

    Purpose:
        Balances the potential reward against the risk taken in each trade.

    Effect:
        A higher ratio (e.g., 3) widens the take profit (TP) area, while a lower ratio (e.g., 1.5) 
        narrows it.

    How to Test:
        - Set to 3 for aggressive trades with wider TP targets.
        - Set to 1.5 for conservative trades with tighter TP targets.
"""

DEFAULT_BUFFER_PIPS = 5
"""
DEFAULT_BUFFER_PIPS:
    A buffer in pips added to trade entries to avoid noise or slippage. This ensures trades 
    are placed with a margin of safety.

    Purpose:
        Adds extra space around stop loss (SL) and take profit (TP) levels to reduce the impact 
        of market noise.

    Effect:
        Increasing this value widens both SL and TP areas slightly, while decreasing it narrows them.

    How to Test:
        - Increase to 15 pips for volatile markets.
        - Decrease to 5 pips for quieter markets.
"""

# ===============================
# Risk-to-Reward Ratios
# ===============================
HIGH_RISK_RATIO = 2
"""
HIGH_RISK_RATIO:
    Used for high-risk trades where the potential reward is greater. A ratio of 3 means 
    the trader aims for 3 units of profit for every 1 unit risked.

    Purpose:
        Provides flexibility for aggressive trading strategies with higher profit targets.

    Effect:
        Widens the take profit (TP) area significantly compared to the stop loss (SL).

    How to Test:
        Use this ratio for trades in trending markets with strong momentum.
"""

LOW_RISK_RATIO = 2
"""
LOW_RISK_RATIO:
    Used for conservative trades with lower potential rewards. A ratio of 2 means the trader 
    aims for 2 units of profit for every 1 unit risked.

    Purpose:
        Offers a balanced approach for low-risk trades with moderate profit targets.

    Effect:
        Narrows the take profit (TP) area relative to the stop loss (SL).

    How to Test:
        Use this ratio for range-bound or choppy markets with limited price movement.
"""

# ===============================
# Technical Indicator Settings
# ===============================
ATR_PERIOD = 14
"""
ATR_PERIOD:
    The period used for calculating the Average True Range (ATR), which measures market volatility. 
    A standard value of 14 periods is commonly used.

    Purpose:
        Quantifies market volatility to adjust stop loss and take profit levels dynamically.

    Effect:
        A longer period (e.g., 20) smooths out volatility, leading to wider SL and TP distances. 
        A shorter period (e.g., 10) makes SL and TP more sensitive to recent price movements.

    How to Test:
        Adjust the ATR period to observe how volatility impacts SL and TP placement.
"""

RSI_PERIOD = 14
"""
RSI_PERIOD:
    The period used for calculating the Relative Strength Index (RSI), which identifies overbought 
    and oversold conditions. A standard value of 14 periods is widely accepted.

    Purpose:
        Detects overbought and oversold conditions to inform entry and exit points.

    Effect:
        A longer period reduces sensitivity, while a shorter period increases responsiveness.

    How to Test:
        Experiment with values like 7 (short-term) or 21 (long-term) to fine-tune RSI signals.
"""

ADX_THRESHOLD = 20
"""
ADX_THRESHOLD:
    The threshold for the Average Directional Index (ADX) to determine trend strength. Values above 
    20 indicate a strong trend.

    Purpose:
        Identifies whether the market is trending or ranging.

    Effect:
        Values above 20 suggest a strong trend, while values below 20 indicate a weak or sideways market.

    How to Test:
        Adjust the threshold to identify trends in different market conditions.
"""

MOVING_AVERAGE_PERIODS = {"short": 7, "mid": 14, "long": 89, "very_long": 200}
"""
MOVING_AVERAGES:
    A list of moving average periods used for trend analysis. These include short-term (7, 14), 
    medium-term (89), and long-term (200) averages.

    Purpose:
        Provides insights into short-, medium-, and long-term trends.

    Effect:
        Shorter periods react quickly to price changes, while longer periods smooth out noise.

    How to Test:
        Add or remove periods to focus on specific timeframes (e.g., add 50 for intermediate trends).
"""

# ===============================
# System Configuration
# ===============================
CAT_TIMEZONE = pytz.timezone("Africa/Harare")
"""
CAT_TIMEZONE:
    The timezone for Central Africa Time (CAT). Used for timestamping and scheduling tasks.

    Purpose:
        Ensures all timestamps and scheduled tasks align with the specified timezone.

    Effect:
        Prevents time-related errors when running automated trading systems.

    How to Test:
        Change to another timezone (e.g., UTC) to verify system behavior.
"""

SYMBOLS_AND_TABLES = {
    "frxEURUSD": "eurousd_candles",
    "frxGBPUSD": "gbpusd_candles",
    "OTC_AS51": "austraila200_candles",
    "frxUSDJPY": "usdjpy_candles",
    "OTC_SPC": "us500_candles",
    "R_75": "v75_candles",
    "frxXAUUSD": "gold_candles"
}
"""
SYMBOLS_AND_TABLES:
    Maps trading symbols to their corresponding database table names. This allows for easy 
    retrieval and storage of historical data.

    Purpose:
        Simplifies data access by associating symbols with their respective tables.

    Effect:
        Ensures accurate data mapping for backtesting and live trading.

    How to Test:
        Add new symbols and verify that data retrieval works as expected.
"""

STRATEGY_TYPES = ["Moving Average", "Malaysian"]
"""
STRATEGY_TYPES:
    A list of supported trading strategies. Currently includes only the "Malaysian" strategy.

    Purpose:
        Specifies the available trading strategies for the system.

    Effect:
        Limits the strategies that can be executed unless expanded.

    How to Test:
        Add additional strategies (e.g., "Malaysian") to test multiple approaches.
"""

SLEEP_DURATION = 4 * 3600  # Sleep duration between iterations (4 hours in seconds)
"""
SLEEP_DURATION:
    The duration (in seconds) the system will sleep between iterations. Set to 4 hours (14400 seconds).

    Purpose:
        Controls the frequency of system checks or iterations.

    Effect:
        Longer durations reduce resource usage but delay responsiveness.

    How to Test:
        Reduce to 1 hour (3600 seconds) for faster testing or increase to 8 hours (28800 seconds) 
        for slower execution.
"""

MAX_RETRIES = 3
"""
MAX_RETRIES:
    The maximum number of retries allowed for transient failures (e.g., network issues).

    Purpose:
        Handles temporary errors gracefully without crashing the system.

    Effect:
        Limits the number of retry attempts to prevent infinite loops.

    How to Test:
        Simulate network failures to verify retry behavior.
"""

# ===============================
# Console Output Colors
# ===============================
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
"""
Console Colors:
    ANSI escape codes for colored console output. These are used to enhance readability of logs 
    and debugging messages.

    Purpose:
        Improves the visibility of important messages in the console.

    Effect:
        Makes error messages (red), success messages (green), and warnings (yellow) stand out.

    How to Test:
        Print messages using these colors to ensure proper formatting.
"""