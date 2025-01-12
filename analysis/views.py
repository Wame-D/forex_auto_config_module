from django.http import JsonResponse
from django.views.decorators.http import require_GET
import asyncio
from datetime import datetime, timedelta
from .analysis_module import fetch_and_analyze_forex_data

@require_GET
async def perform_analysis(request):
    """
    Trigger forex data analysis based on the Malaysian Forex Strategy.
    Allows passing an optional 'start_time' parameter.
    
    Parameters:
        - start_time (str): The starting point for the analysis in "YYYY-MM-DD HH:MM:SS" format.
          Defaults to the last 24 hours from the current time if not provided.
    
    Returns:
        JsonResponse: A JSON response with the detailed analysis results.
    """
    # Fetch start_time from request, default to last 24 hours if not provided
    start_time_str = request.GET.get('start_time', None)
    
    if start_time_str:
        start_time = start_time_str.strip()  # Remove unwanted spaces or newlines
    else:
        # Default to the last 24 hours from the current time
        start_time = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"[DEBUG] Starting analysis with start_time: {start_time}")
    
    try:
        # Ensure the function is called asynchronously with the provided start_time
        analysis_output = await fetch_and_analyze_forex_data(start_time)
        
        # Return the detailed analysis output in the response
        if not analysis_output:
            return JsonResponse({"status": "error", "message": "No data available for the given time range."}, status=404)
    
        print(f"[DEBUG] Analysis completed: {analysis_output}")
        return JsonResponse({"status": "success", "message": "Analysis completed.", "data": analysis_output}, status=200)
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return JsonResponse(
            {"status": "error", "message": f"An error occurred: {str(e)}"},
            status=500
        )
