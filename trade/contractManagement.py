import asyncio
import websockets
import json
from websocket import create_connection
from deriv_api import DerivAPI

async def fetch_contract_updates(contract_id, api_token, app_id):
    """
    Fetches contract updates continuously until the contract ends.
    """
    api = DerivAPI(app_id=app_id)

    try:
        # Authorize the API connection
        await api.authorize(api_token)
        print("Authorized successfully.")

        updates = []  # To store contract updates
        # while True:
        try:
            # Send the proposal_open_contract request
            response = await api.send({
                "proposal_open_contract": 1,
                "contract_id": contract_id
            })

            # Add the response to updates
            updates.append(response)

            # Print the contract details
            print(f"Contract details for ID {contract_id}:")
            # print(response)

            # Check if the contract has ended
            if response.get("is_expired"):
                print("Contract has ended.")
                # break

        except Exception as e:
            print(f"Error fetching contract details: {e}")
            updates.append({"error": str(e)})
            # break

        # Wait for 2 seconds before fetching updates again
        # await asyncio.sleep(2)

        return response

    except Exception as e:
        print(f"Authorization error: {e}")
        return {"error": str(e)}

    finally:
        # Disconnect from the API
        await api.disconnect()
        print("Disconnected from Deriv API")