from datetime import datetime, timedelta
import pytz  
import asyncio
import threading

import schedule
import time
from django.http import JsonResponse
from django.test import RequestFactory
from .views import get_risks
from .views import get_profit_and_loss_margin
import json
from forex.clickhouse.connection import get_clickhouse_client
from django_cron import CronJobBase, Schedule
from authorise_deriv.views import balance
# Initialize ClickHouse client
client = get_clickhouse_client()

# ANSI escape codes for colors
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'  # Reset to default color
today_date = datetime.now().strftime('%Y-%m-%d')

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

    win_per_day = win_loss[0][4]
    loss_per_day = win_loss[0][2]
    overall_loss = win_loss[0][3]
    overall_win = win_loss[0][5]

    number_of_trade_per_day = risk_per_day / risk_per_trade
    # check if user's trade has exceeded his trades per day
    result = client.query(f"""
        SELECT COUNT(*) AS row_count, SUM(win) AS total_win, SUM(loss) AS total_loss
        FROM trades
        WHERE email = '{email}' 
        AND DATE(timestamp) = '{today_date}'
    """)

    trade_count = result.result_set[0][0]
    win = result.result_set[0][1] or 0.0  # Default to 0 if None
    loss = result.result_set[0][2] or 0.0 

    # fetching alance that the user has by the start of  today
    balance_data = client.query(f"""
        SELECT balance_today, balance
        FROM userdetails
        WHERE email = '{email}' 
    """)
    balance_day =  [row[0] for row in balance_data.result_set]
    total_balance =  [row[1] for row in balance_data.result_set]

    if trade_count >= number_of_trade_per_day:
        trading = 'false'
        client.command(f"""
            ALTER TABLE userdetails UPDATE trading_today = {trading}
            WHERE email = '{email}'
        """)
        print(f"{YELLOW}[INFO] trades for user {email} exceeded the limit.{RESET}")
        return 'false'
    else:
        # cheking if loss or win has exceeded his / her choice
        loss_day = balance_day[0] * (loss_per_day / 100)
        win_day = balance_day[0] * (win_per_day / 100)
        overall_win = total_balance[0] * (overall_win /100)
        overall_loss = total_balance[0] * (overall_loss/100)

        if (loss_day <= loss or win_day <= win):
            trading = 'false'
            client.command(f"""
                ALTER TABLE userdetails UPDATE trading_today = {trading}
                WHERE email = '{email}'
            """)

            # Use the color in the print statement
            print(f"{YELLOW}[INFO] loss or win for user {email} exceeded the limit, not trading today Trade skipped.{RESET}")
            return 'false'
        elif total_loss >= overall_loss or total_win >=  overall_win:
            trading = 'false'
            client.command(f"""
                ALTER TABLE userdetails UPDATE trading_today = {trading}, trading = {trading}
                WHERE email = '{email}'
            """)
            # Use the color in the print statement
            print(f"{YELLOW}[INFO] overall loss or win for user {email} exceeded the limit, not trading today Trade skipped.{RESET}")
            return 'false'
        else:
            return 'true'

"""
adding a method to reset settings to default at every 11:00pm

stop bot for users who set the bot to stop at that date
when overall win and loss have reached

update todays balance
"""

# Set up logging
import logging
logging.basicConfig(filename='/path/to/logfile.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def auto_config():
    logging.info(f"_________________________________________________________________________________________________________________")
    logging.info(f"{BLUE}Running auto_config at {datetime.now()}{RESET}")
    logging.info(f"_________________________________________________________________________________________________________________")


    # shuting dow all users who set stop time to today
    trading = 'false'
    client.command(f"""
        ALTER TABLE userdetails UPDATE trading_today = {trading}, trading = {trading}
        WHERE DATE(stop_date) = '{today_date}'
    """)

    # resume trading for all users who were temporariry disabled to to risk limit and win or loss marging
    client.command(f"""
        ALTER TABLE userdetails UPDATE trading_today = 'true'
        WHERE trading = 'true'
    """)

    # updating user alance at 12:00 mid night
    result = client.query(f"""
        SELECT token
        FROM userdetails
        WHERE trading = 'true'
    """)

    # tokens = result.result_set[0][0]
    tokens = [row[0] for row in result.result_set]

    for token in  tokens:
        # getting balance and updating it
        try:
            account_balance = balance(token)
            # updating balance
            client.command(f"""
                ALTER TABLE userdetails UPDATE balance_today = {account_balance}
                WHERE token = {token}
            """)
        except Exception as e:
            print(f"[ERROR] Error updating balances: {e}")
            logging.error(f"Error updating balance: {e}")

