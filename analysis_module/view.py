import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .analysis import fetch_forex_data, aggregate_data, analyze_malaysian_strategy

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@csrf_exempt
def forex_analysis(request):
    """
    View to trigger the forex analysis and return generated trading signals as a JSON response.
    """
    try:
        # Fetch and prepare data
        df_minute = fetch_forex_data(request)
        if not df_minute:  # Check if the list is empty or None
            return JsonResponse({"error": "Failed to fetch forex data"}, status=500)

        # Aggregate the data into 4-hour and 15-minute timeframes
        df_4h = aggregate_data(df_minute, "4H")
        df_15m = aggregate_data(df_minute, "15M")

        # Apply the strategy to generate trading signals
        signals = analyze_malaysian_strategy(df_4h, df_15m)

        # Return the result as JSON
        if signals:
            return JsonResponse({"signals": signals}, safe=False)
        else:
            return JsonResponse({"error": "No valid trading signals generated."}, status=200)

    except Exception as e:
        logger.exception(f"An error occurred in forex_analysis: {e}")
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
