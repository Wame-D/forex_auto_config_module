
from django.core.management.base import BaseCommand
from datetime import datetime
import logging
from forex.clickhouse.connection import get_clickhouse_client

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m' 
class Command(BaseCommand):
    help = 'Runs the auto configuration task every day at 11:00 PM'

    def handle(self, *args, **kwargs):
        logging.basicConfig(filename='/logfile.log', level=logging.INFO, format='%(asctime)s - %(message)s')
        client = get_clickhouse_client()
        today_date = datetime.today().date()  # Get today's date
        logging.info(f"_________________________________________________________________________________________________________________")
        logging.info(f"{BLUE}Running auto_config at {datetime.now()}{RESET}")
        logging.info(f"_________________________________________________________________________________________________________________")


        result = client.query(f"""
            SELECT email, stop_date, start_date
            FROM start_stop_table
            WHERE DATE(stop_date) = '{today_date}'
        """)

        for row in result.result_set:
            print("emai fetched")
            email, stop_date,  start_date= row[0] ,row[1], row[2]
            # getting balance and updating it
            try:
                if stop_date == today_date:
                    trading = 'false'
                    client.command(f"""
                        ALTER TABLE userdetails UPDATE trading_today = {trading}, trading = {trading}
                        WHERE email = '{email }'
                    """)

                elif start_date ==   today_date:
                    trading = 'true'
                    client.command(f"""
                        ALTER TABLE userdetails UPDATE trading_today = {trading}, trading = {trading}
                        WHERE email = '{email }'
                    """)
            except Exception as e:
                print(f"[ERROR] Error updating balances: {e}")
                logging.error(f"Error updating balance: {e}")
        # shuting dow all users who set stop time to today
    

        # resume trading for all users who were temporariry disabled to to risk limit and win or loss marging
        client.command(f"""
            ALTER TABLE userdetails UPDATE trading_today = 'true'
            WHERE trading = 'true'
        """)

        # updating user alance at 12:00 mid night
        result1 = client.query(f"""
            SELECT token,email
            FROM userdetails
            WHERE trading = 'true'
        """)

        for row in result1.result_set:
            token, email = row[0],row[1]
            print(f"token fetched: {token}")
            # getting balance and updating it
            try:
                account_balance = balance(token)
                # updating balance
                client.command(f"""
                    ALTER TABLE userdetails UPDATE balance_today = {account_balance}
                    WHERE token = {token}
                """)

                create_table_query = f"""
                CREATE TABLE IF NOT EXISTS balances (
                    timestamp DateTime,
                    balance Float32,
                    email String,
                ) ENGINE = MergeTree()
                ORDER BY timestamp
                 """
                client.command(create_table_query)

                # Insert the candle into the table
                insert_query = f"""
                    INSERT INTO balances (timestamp, balance, email)
                    VALUES (NOW(), {account_balance},{email})
                """
                client.command(insert_query)
            except Exception as e:
                print(f"[ERROR] Error updating balances: {e}")
                logging.error(f"Error updating balance: {e}")

