from datetime import datetime

# Sample data for analysis
forex_data = [
    {
        "timestamp": "2024-12-29T11:00:00Z",
        "open": 134.50,
        "high": 134.60,
        "low": 134.45,
        "close": 134.55,
        "volume": 1000
    },
    # Add more data as needed...
]

def find_key_patterns(data):
    key_patterns = []
    
    for i in range(1, len(data)):
        current = data[i]
        previous = data[i-1]
        
        # Find a bearish followed by a bullish (support) or bullish followed by a bearish (resistance) pattern
        if previous['close'] > previous['open'] and current['close'] < current['open']:  # Bearish followed by Bullish (Support)
            key_patterns.append({"pattern": "support", "timestamp": current["timestamp"]})
        elif previous['close'] < previous['open'] and current['close'] > current['open']:  # Bullish followed by Bearish (Resistance)
            key_patterns.append({"pattern": "resistance", "timestamp": current["timestamp"]})
    
    return key_patterns

def draw_safe_zone(data, pattern):
    if pattern['pattern'] == "support":
        entry_price = data[-1]['close'] + 0.02  # Add 2 pips
        safe_zone = {"entry": entry_price, "stop_loss": entry_price - 0.04}
    elif pattern['pattern'] == "resistance":
        entry_price = data[-1]['close'] - 0.02  # Subtract 2 pips
        safe_zone = {"entry": entry_price, "stop_loss": entry_price + 0.04}
    
    return safe_zone

def perform_analysis(forex_data):
    patterns = find_key_patterns(forex_data)
    analysis_results = []
    
    for pattern in patterns:
        safe_zone = draw_safe_zone(forex_data, pattern)
        analysis_results.append({"pattern": pattern, "safe_zone": safe_zone})
    
    return analysis_results

# Perform analysis
analysis_results = perform_analysis(forex_data)

for result in analysis_results:
    print(f"Pattern: {result['pattern']['pattern']} at {result['pattern']['timestamp']}")
    print(f"Safe Zone: Entry at {result['safe_zone']['entry']} | Stop Loss at {result['safe_zone']['stop_loss']}")
    print()
