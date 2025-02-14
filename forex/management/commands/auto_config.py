from django.core.management.base import BaseCommand
from datetime import datetime
from forex.clickhouse.connection import get_clickhouse_client
import os
import logging

# Ensure the logs directory exists
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Setup logging to log to the logs directory
logfile = os.path.join(log_dir, 'auto_config.log')

logging.basicConfig(
    filename=logfile,
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class Command(BaseCommand):
    help = 'Runs the auto configuration task every day at 11:00 PM'

    def handle(self, *args, **kwargs):
        client = get_clickhouse_client()
        today_date = datetime.today().date()  # Get today's date
        logging.info(f"_________________________________________________________________________________________________________________")
        logging.info(f"{BLUE}Running auto_config at {datetime.now()}{RESET}")
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
            logging.info("Successfully updated the stop/start dates for users.")

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

                insert_query = f"""
                    INSERT INTO balances (timestamp, balance, email)
                    VALUES (NOW(), {account_balance}, {email})
                """
                client.command(insert_query)

            logging.info("Successfully updated balances.")
        except Exception as e:
            logging.error(f"Error running auto_config: {e}")
