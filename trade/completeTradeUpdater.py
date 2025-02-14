from forex.clickhouse.connection import get_clickhouse_client

def update_trade_status(contract_id, trade_status, sell_time, sell_price, profit_loss, buy_price):
    """Updates the trade status and additional fields in the ClickHouse database."""
    try:
        client = get_clickhouse_client()
        update_query = f'''
            ALTER TABLE trades UPDATE 
                trade_status = '{trade_status}',
                sell_time = '{sell_time}',
                sell_price = {sell_price},
                profit_loss = {profit_loss},
                buy_price = {buy_price}
            WHERE contract_id = {contract_id};
        '''
        client.command(update_query)
        print(f"Trade {contract_id} updated to status: {trade_status}, buy_price: {buy_price}, sell_price: {sell_price}, profit/loss: {profit_loss}")
    except Exception as e:
        print(f"Failed to update trade status: {e}")
