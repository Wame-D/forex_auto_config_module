from django.http import JsonResponse
from django.views.decorators.http import require_GET
import asyncio
from .analysis_module import fetch_and_analyze_forex_data

@require_GET
async def perform_analysis(request):
    """
    Trigger forex data analysis based on the Malaysian Forex Strategy.
    Allows passing an optional 'start_time' parameter.
    
    Parameters:
        - start_time (str): The starting point for the analysis in "YYYY-MM-DD HH:MM:SS" format.
          Defaults to "2025-01-01 00:00:00" if not provided.
    
    Returns:
        JsonResponse: A JSON response indicating success or failure.
    """
    start_time = request.GET.get('start_time', '2025-01-01 00:00:00')  # Default start time

    try:
        # Ensure the function is called asynchronously
        await fetch_and_analyze_forex_data(start_time)
        return JsonResponse({"status": "success", "message": "Analysis completed."}, status=200)
    except Exception as e:
        # Return an error response with details
        return JsonResponse(
            {"status": "error", "message": f"An error occurred: {str(e)}"},
            status=500
        )
