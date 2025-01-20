async def fetch_profit_table(token, options=None):
    """
    Fetch the Profit Table from the Deriv API.

    :param token: Your authorized API token with 'readtrading_information' permission.
    :param options: Optional dictionary for profit table request parameters.
                    - limit (int): The maximum number of transactions to retrieve (default is 50).
                    - sort (str): Sorting order ('ASC' or 'DESC', default is 'DESC').
                    - description (bool): Whether to include full contract descriptions (default is False).
                    - date_from (str): Start date (optional).
                    - date_to (str): End date (optional).
    :return: The profit table data as a dictionary.
    """
    # Default options
    options = options or {}
    limit = options.get("limit", 50)
    sort = options.get("sort", "DESC")
    description = 1 if options.get("description", False) else 0
    date_from = options.get("date_from", "")
    date_to = options.get("date_to", "")

    # Deriv WebSocket URL
    url = "wss://ws.binaryws.com/websockets/v3?app_id=65102"

    # WebSocket connection
    async with websockets.connect(url) as websocket:
        # Step 1: Authenticate
        auth_message = {
            "authorize": token
        }
        await websocket.send(json.dumps(auth_message))

        # Wait for the authorization response
        auth_response = await websocket.recv()
        auth_data = json.loads(auth_response)
        if "error" in auth_data:
            raise Exception(f"Authorization failed: {auth_data['error']['message']}")

        print("Authorization successful.")

        # Step 2: Request Profit Table
        profit_table_message = {
            "profit_table": 1,
            "limit": limit,
            "sort": sort,
            "description": description,
            "date_from": date_from,
            "date_to": date_to
        }
        await websocket.send(json.dumps(profit_table_message))

        # Wait for the profit table response
        profit_table_response = await websocket.recv()
        profit_table_data = json.loads(profit_table_response)

        # Check if there's an error in the response
        if "error" in profit_table_data:
            raise Exception(f"Error fetching profit table: {profit_table_data['error']['message']}")

        # Step 3: Return the profit table data
        return profit_table_data.get("profit_table", {})