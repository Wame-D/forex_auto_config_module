from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache  # Ensure this import is present for caching
from .forex_data import forex_data
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
