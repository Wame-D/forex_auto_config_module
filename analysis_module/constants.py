# Configuration Constants
TIMEFRAMES = {
    "4H": 240,    # 4-hour chart
    "15M": 15     # 15-minute chart
}

PIP_VALUE = 0.0001  # Example for EUR/USD
RISK_PERCENTAGE = 1  # Risk 1% of account balance per trade
REWARD_TO_RISK_RATIO = 2  # Example R:R = 2:1
DEFAULT_BUFFER_PIPS = 10  # Buffer for stop loss
EXOTIC_PAIRS = ["USD/TRY", "EUR/ZAR"]  # High-risk pairs to avoid
# Risk ratios for different trade types
HIGH_RISK_RATIO = 3  # Example for high-risk trades (1:3 R:R)
LOW_RISK_RATIO = 2   # Example for low-risk trades (1:2 R:R)
