from django.shortcuts import render
from crown_api.director_router import get_director_persona, get_director_filter_config

def director_dashboard_page(request, persona=None):
    """
    Serve the Director Dashboard HTML page with persona-based context.
    
    Supports both:
    - /director/ → Auto-detect persona from user's role
    - /director/admissions/ → Explicit persona from URL
    """
    # Use URL persona if provided, otherwise detect from user
    if not persona:
        persona = get_director_persona(request.user)
    
    filter_config = get_director_filter_config(persona)
    
    context = {
        'persona': persona,
        'page_title': filter_config['title'],
        'filter_config': filter_config,
        'api_endpoints': {
            'dashboard': '/api/director/dashboard/',
            'priority': '/api/director/priority/',
            'timeline': '/api/director/timeline/',
            'actions': '/api/director/actions/',
        }
    }
    
    return render(request, "director_dashboard.html", context)
