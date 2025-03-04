import asyncio
from datetime import datetime
from .connection import get_clickhouse_client

# ANSI escape codes for colors
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'  # Reset to default color


async def auto_trading_monitor():
    client = get_clickhouse_client()
    today_date = datetime.today().date()
    print(f"{BLUE}Running auto_trading_monitor at {datetime.now()}{RESET}")

    try:
        user_query = client.query(f"""
            SELECT u.email, u.token, u.balance, u.balance_today,
                   r.per_trade, r.per_day,
                   s.loss_per_day, s.overall_loss, s.win_per_day, s.overall_win
            FROM userdetails AS u
            JOIN risk_table AS r ON u.email = r.email
            JOIN start_stop_table AS s ON u.email = s.email
            WHERE u.trading = '1'
        """)
        # print(f"{YELLOW} first uery resuly: {user_query.result_set} {RESET}")
        for row in user_query.result_set:
            email, token, balance, balance_today, per_trade, per_day, loss_per_day, overall_loss, win_per_day, overall_win = row
            
            # Calculate balance change
            profit_loss_query = client.query(f"""
                SELECT SUM(profit_loss)
                FROM trades
                WHERE email = '{email}' AND DATE(timestamp) = '{today_date}'
            """)
            # Check if profit_loss is None and default to 0 if so
            total_profit_loss = profit_loss_query.result_set[0][0] if profit_loss_query.result_set and profit_loss_query.result_set[0][0] is not None else 0
            
            # Check daily limits
            if total_profit_loss <= -abs(loss_per_day * balance / 100) or total_profit_loss >= abs(win_per_day * balance / 100):
                trading = 'false'
                client.command(f"""
                    ALTER TABLE userdetails UPDATE trading_today = {trading}
                    WHERE email = '{email}'
                """)
                print(f"{YELLOW}{email} has reached daily limits. Trading today disabled.{RESET}")
            
            # Check overall limits
            overall_profit_loss_query = client.query(f"""
                SELECT SUM(profit_loss)
                FROM trades
                WHERE email = '{email}'
            """)
            # Check if overall_profit_loss is None and default to 0 if so
            total_overall_profit_loss = overall_profit_loss_query.result_set[0][0] if overall_profit_loss_query.result_set and overall_profit_loss_query.result_set[0][0] is not None else 0
            
            if total_overall_profit_loss <= -abs(overall_loss * balance / 100) or total_overall_profit_loss >= abs(overall_win * balance / 100):
                trading = 'false'
                client.command(f"""
                    ALTER TABLE userdetails UPDATE trading = {trading}, trading_today = {trading}
                    WHERE email = '{email}'
                """)
                print(f"{RED}{email} has reached overall limits. Trading permanently disabled.{RESET}")

        print(f"{GREEN}Balance and trading status updated successfully.{RESET}")

    except Exception as e:
        print(f"{RED}Error running auto_trading_monitor: {e}{RESET}")
    
    print(f"{BLUE}Sleeping for 2 minutes before next check...{RESET}")
    await asyncio.sleep(120)  # Sleep for 2 minutes
    await auto_trading_monitor()  # Recursively call the function


