from datetime import datetime, timedelta
import pytz  
import time
from django.http import JsonResponse
from django.test import RequestFactory
from .views import get_risks
from .views import get_profit_and_loss_margin
import json
from forex.clickhouse.connection import get_clickhouse_client
# from django_cron import CronJobBase, Schedule
from authorise_deriv.views import balance
from trade.tradeHistory import fetch_profit_table
# Initialize ClickHouse client
client = get_clickhouse_client()
# ANSI escape codes for colors
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'  # Reset to default color
today_date = datetime.now().strftime('%Y-%m-%d')

async def eligible_user(email,token):
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
    date_from = win_loss[0][0]
    date_to = today_date

    number_of_trade_per_day = risk_per_day / risk_per_trade
    # check if user's trade has exceeded his trades per day
    # fetch trade total history
    date_from = datetime.strptime(date_from, "%Y-%m-%dT%H:%M:%S")
    date_from = date_from.strftime("%Y-%m-%d")
    options = {
        "limit": 10,  # Limit to 10 transactions
        "sort": "DESC",  # Sort by most recent transactions
        "description": True,  # Include contract descriptions
        "date_from": date_from,  # Calculated start date
        "date_to": today_date,  # Calculated end date
    }
    history = await fetch_profit_table(token, options)
    total_loss = history['stats']['total_loss']
    total_win = history['stats']['total_profit']

    # per day history
    options1 = {
        "limit": 10,  # Limit to 10 transactions
        "sort": "DESC",  # Sort by most recent transactions
        "description": True,  # Include contract descriptions
        "date_from": today_date,  # Calculated start date
        "date_to": today_date,  # Calculated end date
    }
    today_history = await fetch_profit_table(token, options1)
    trade_count = today_history['profit_table']['count']
    loss = today_history['stats']['total_loss']
    win = today_history['stats']['total_profit']

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
        # print(f"{YELLOW}[INFO] trades for user {email} exceeded the limit.{RESET}")
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
            # print(f"{YELLOW}[INFO] loss or win for user {email} exceeded the limit, not trading today Trade skipped.{RESET}")
            return 'false'
        elif total_loss >= overall_loss or total_win >=  overall_win:
            trading = 'false'
            client.command(f"""
                ALTER TABLE userdetails UPDATE trading_today = {trading}, trading = {trading}
                WHERE email = '{email}'
            """)
            # Use the color in the print statement
            # print(f"{YELLOW}[INFO] overall loss or win for user {email} exceeded the limit, not trading today Trade skipped.{RESET}")
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
logging.basicConfig(filename='/logfile.log', level=logging.INFO, format='%(asctime)s - %(message)s')

import asyncio

async def auto_config():
    client = get_clickhouse_client()
    today_date = datetime.today().date()  # Get today's date
    logging.info(f"_________________________________________________________________________________________________________________")
    print(f"{BLUE}Running auto_config at {datetime.now()}{RESET}")
    logging.info(f"_________________________________________________________________________________________________________________")

    try:
        result = client.query(f"""
            SELECT email, stop_date, start_date
            FROM start_stop_table
            WHERE DATE(stop_date) = '{today_date}'
        """)

        for row in result.result_set:
            email, stop_date, start_date = row[0], row[1], row[2]
            if stop_date == today_date:
                trading = 'false'
                client.command(f"""
                    ALTER TABLE userdetails UPDATE trading_today = {trading}, trading = {trading}
                    WHERE email = '{email }'
                """)
            elif start_date == today_date:
                trading = 'true'
                client.command(f"""
                    ALTER TABLE userdetails UPDATE trading_today = {trading}, trading = {trading}
                    WHERE email = '{email }'
                """)
                print(f"{BLUE}Running auto_config at, started trading {RESET}")
            else:
                print(f"{BLUE}Running auto_config at, no data updated {RESET}")

        # Resume trading for all users who were temporarily disabled due to risk limit
        client.command(f"""
            ALTER TABLE userdetails UPDATE trading_today = 'true'
            WHERE trading = 'true'
        """)

        # Update user balances
        result1 = client.query(f"""
            SELECT token, email
            FROM userdetails
            WHERE trading = 'true'
        """)

        for row in result1.result_set:
            token, email = row[0], row[1]
            account_balance = balance(token)  # Make sure this function is defined

            client.command(f"""
                ALTER TABLE userdetails UPDATE balance_today = {account_balance}
                WHERE token = {token}
            """)

            create_table_query = f"""
                CREATE TABLE IF NOT EXISTS balances (
                    timestamp DateTime,
                    balance Float32,
                    email String
                ) ENGINE = MergeTree()
                ORDER BY timestamp
            """
            client.command(create_table_query)
            print(f"{BLUE}Running auto_config at, tabble created {RESET}")

            insert_query = f"""
                INSERT INTO balances (timestamp, balance, email)
                VALUES (NOW(), {account_balance}, {email})
            """
            client.command(insert_query)

        logging.info("Successfully updated balances.")

    except Exception as e:
        print(f"Error running auto_config: {e}")
    
    # Sleep for 4 hours before the next run
    logging.info(f"Sleeping for 4 hours...")
    await asyncio.sleep(4 * 60 * 60)  # 4 hours in seconds

    # Call the function again after sleeping
    await auto_config()  # Recursively call the function

# To run auto_config asynchronously
async def run_auto_config():
    await auto_config()
