from authorise_deriv.views import balance
import asyncio
from datetime import datetime
from .connection import get_clickhouse_client

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m' 

async def balance__tracker():
    client = get_clickhouse_client()

    print("")
    print(f"{BLUE}___________________________________ BALANCE TRACKER____________________________________{RESET}")
    print("")
    print(f"{BLUE}Running balance__tracker at {datetime.now()}{RESET}")
    print("")

    try:
        
        # Update balances
        result1 = client.query(f"""
            SELECT token, email
            FROM userdetails
        """)

        for row in result1.result_set:
            token, email = row[0], row[1]

            account_balance = await balance(token) 
            print(f"{BLUE}Updating balance for {email} = {account_balance} {RESET}")
            client.command(f"""
                ALTER TABLE userdetails UPDATE balance_today = {account_balance}
                WHERE token = '{token}'
            """)

            client.command("""
                CREATE TABLE IF NOT EXISTS balances (
                    timestamp DateTime,
                    balance Float32,
                    email String
                ) ENGINE = MergeTree()
                ORDER BY timestamp
            """)
            
            client.command(f"""
                INSERT INTO balances (timestamp, balance, email)
                VALUES (NOW(), {account_balance}, '{email}')
            """)

        print(f"{GREEN}Successfully updated balances.{RESET}")

    except Exception as e:
        print(f"{RED}Error running auto_config: {e}{RESET}")
        raise

    # Sleep for 2 before rerunning
    print(f"{BLUE}Sleeping for 2 hours...{RESET}")
    await asyncio.sleep(60 * 60 * 2)
    await balance__tracker()
