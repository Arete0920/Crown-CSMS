from django.shortcuts import render
from crown_api.director_router import route_director_view

def director_dashboard_page(request):
    """
    Serve the Director Dashboard HTML page with persona-based context.
    
    Uses director_router to determine which sections to emphasize
    based on the user's role (Aid Director, Admissions Director, etc.)
    """
    routing = route_director_view(request)
    
    context = {
        'persona': routing['persona'],
        'page_title': routing['config']['title'],
        'filter_config': routing['config'],
        'api_endpoints': routing['api_endpoints'],
    }
    
    return render(request, "director_dashboard.html", context)
