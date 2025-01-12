import datetime
import random

def generate_random_price(base_price, range_span=10):
    """Generate a random price within a certain range from the base price."""
    return round(random.uniform(base_price - range_span, base_price + range_span), 2)

def generate_historical_data(start_date, end_date, interval_minutes=30):
    """Generate forex data at fixed intervals between the start and end datetime."""
    rows = []
    current_time = start_date
    while current_time <= end_date:
        # Simulating market fluctuations for XAU/USD
        open_price = generate_random_price(1050)  # Base price can be adjusted
        high_price = round(open_price + random.uniform(1, 10), 2)
        low_price = round(open_price - random.uniform(1, 10), 2)
        close_price = round(random.uniform(low_price, high_price), 2)

        rows.append((current_time, open_price, high_price, low_price, close_price))
        current_time += datetime.timedelta(minutes=interval_minutes)

    return rows

def format_data_for_api(rows):
    """Convert raw data into a list of dictionaries formatted for API use."""
    return [
        {
            "timestamp": row[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "open": row[1],
            "high": row[2],
            "low": row[3],
            "close": row[4],
        }
        for row in rows
    ]

def forex_data():
    """Return sample predefined XAU/USD forex data as a list of dictionaries."""
    try:
        # Define date range for historical data
        start_date = datetime.datetime(2025, 1, 10, 0, 0, 0)
        end_date = datetime.datetime(2025, 1, 12, 23, 59, 59)

        # Generate historical forex data (48 data points, every 30 minutes)
        raw_data = generate_historical_data(start_date, end_date)
        
        # Convert raw data into desired format
        return format_data_for_api(raw_data)

    except Exception as e:
        print(f"[ERROR] Error fetching data: {e}")
        return []

def generate_predefined_data():
    """Generate a list of predefined XAU/USD forex data."""
    rows = [
        (datetime.datetime(2025, 1, 10, 0, 0, 0), 1025.35, 1030.56, 1023.50, 1027.70),
        (datetime.datetime(2025, 1, 10, 4, 0, 0), 1028.76, 1032.50, 1026.45, 1031.23),
        (datetime.datetime(2025, 1, 10, 8, 0, 0), 1031.23, 1034.88, 1030.12, 1032.76),
        (datetime.datetime(2025, 1, 10, 12, 0, 0), 1033.00, 1037.90, 1031.60, 1035.20),
        (datetime.datetime(2025, 1, 10, 16, 0, 0), 1035.20, 1040.50, 1032.80, 1038.45),
        (datetime.datetime(2025, 1, 10, 20, 0, 0), 1038.45, 1043.10, 1037.00, 1040.75),
        (datetime.datetime(2025, 1, 11, 0, 0, 0), 1040.75, 1045.60, 1038.90, 1043.50),
        (datetime.datetime(2025, 1, 11, 4, 0, 0), 1043.50, 1050.40, 1042.20, 1047.80),
        (datetime.datetime(2025, 1, 11, 8, 0, 0), 1047.80, 1055.20, 1045.30, 1050.60),
        (datetime.datetime(2025, 1, 11, 12, 0, 0), 1050.60, 1057.90, 1049.10, 1054.80),
        (datetime.datetime(2025, 1, 11, 16, 0, 0), 1054.80, 1060.00, 1052.50, 1058.40),
        (datetime.datetime(2025, 1, 11, 20, 0, 0), 1058.40, 1064.70, 1057.10, 1061.50),
        (datetime.datetime(2025, 1, 12, 0, 0, 0), 1061.50, 1066.30, 1060.00, 1063.70),
        (datetime.datetime(2025, 1, 12, 4, 0, 0), 1063.70, 1070.50, 1062.20, 1068.00),
        (datetime.datetime(2025, 1, 12, 8, 0, 0), 1068.00, 1072.40, 1066.80, 1070.60),
        (datetime.datetime(2025, 1, 12, 12, 0, 0), 1070.60, 1075.10, 1069.50, 1072.30),
        (datetime.datetime(2025, 1, 12, 16, 0, 0), 1072.30, 1077.60, 1070.90, 1075.50),
        (datetime.datetime(2025, 1, 12, 20, 0, 0), 1075.50, 1080.80, 1074.00, 1079.20),
    ]
    
    # Return data in API-compatible format
    return format_data_for_api(rows)
