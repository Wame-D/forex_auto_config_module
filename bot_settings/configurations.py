# from .connection import get_clickhouse_client
from datetime import datetime, timedelta
import pytz  # Import pytz for timezone handling
import asyncio
import threading

from django.http import JsonResponse
from django.test import RequestFactory
from .views import get_risks
from .views import get_profit_and_loss_margin
import json
from forex.clickhouse.connection import get_clickhouse_client
# Initialize ClickHouse client
client = get_clickhouse_client()

def eligible_user(email):
    # Simulate a POST request
    factory = RequestFactory()
    request = factory.post('/get_risks/', data={'email': email}, content_type='application/json')
    request1 = factory.post('/get_profit_and_loss/', data={'email': email}, content_type='application/json')

    response = get_risks(request)
    response_content = response.content.decode('utf-8')
    parsed_data = json.loads(response_content)
    risks = parsed_data['risks']
    risk_per_trade = risks[0]
    risk_per_day = risks[1]

    # fetching win loss percentagege
    win_loss_percentage =get_profit_and_loss_margin(request1)
    win_loss_content = win_loss_percentage.content.decode('utf-8')
    win_loss_data = json.loads(win_loss_content)
    win_loss = win_loss_data['data']

    win_per_day = win_loss[4]
    loss_per_day = win_loss[2]

    number_of_trade_per_day = risk_per_day / risk_per_trade
    # check if user's trade has exceeded his trades per day
    today_date = datetime.now().strftime('%Y-%m-%d')
    # Fetch the start_time from the database
    result = client.query(f"""
        SELECT COUNT(*) AS row_count, loss_trade, win_trade
        FROM trades 
        WHERE email = '{email}' 
        AND DATE(timestamp) = '{today_date}'
    """)
    trade_count  = [row[0] for row in result.result_set]
    win = [row[1] for row in result.result_set]
    loss = [row[2] for row in result.result_set]

    # fetching alance that the user has by the start of  today
    balance_data = client.query(f"""
        SELECT balance_today
        FROM userdetails
        WHERE email = '{email}' 
    """)
    balance =  [row[0] for row in balance_data.result_set]

    if trade_count >= number_of_trade_per_day:
        trading = 'false'
        client.command(f"""
            ALTER TABLE userdetails UPDATE trading_today = {trading}
            WHERE email = '{email}'
        """)

        return 'false'
    else:
        # cheking if loss or win has exceeded his / her choice
        loss_day = balance * (loss_per_day / 100)
        win_day = balance * (win_per_day / 100)

        if (loss_day <= loss or win_day <= win):
            trading = 'false'
            client.command(f"""
                ALTER TABLE userdetails UPDATE trading_today = {trading}
                WHERE email = '{email}'
            """)

            return 'false'
        else:
            return 'true'
