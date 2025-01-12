from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache  # Ensure this import is present for caching
from .forex_data import forex_data
from .forex_analysis import fetch_and_analyze_forex_data

# Cache data fetching and returning it as JSON
@csrf_exempt
def forex_data_view(request):
    """Fetch forex data and return it as JSON, with caching."""
    try:
        # Try to get data from cache to improve performance
        data = cache.get('forex_data')

        if not data:
            # If no data is cached, fetch it
            data = forex_data()
            # Cache the data for 60 seconds (adjust the timeout based on your needs)
            cache.set('forex_data', data, timeout=60)
        
        # Return the cached or newly fetched data as JSON
        return JsonResponse(data, safe=False, status=200)

    except Exception as e:
        # Handle any errors that occur during the process
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ForexAnalysisView(View):
    """View to handle Forex analysis and return generated signals."""
    
    async def get(self, request, *args, **kwargs):
        """Handle GET request to trigger Forex analysis."""
        try:
            # Optionally, pass a start time or use the current time (default)
            start_time = request.GET.get("start_time", "2025-01-01 00:00:00")
            
            # Fetch and analyze Forex data based on the given start time
            output_data = await fetch_and_analyze_forex_data()

            
            if output_data:
                # If analysis was successful, return signals as JSON
                return JsonResponse({"status": "success", "data": output_data}, status=200)
            else:
                # If no signals were generated, return an error message
                return JsonResponse({"status": "error", "message": "No valid signals generated."}, status=400)
        
        except Exception as e:
            # Handle any exceptions during the analysis process
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
